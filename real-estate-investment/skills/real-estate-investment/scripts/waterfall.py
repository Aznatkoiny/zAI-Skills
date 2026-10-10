#!/usr/bin/env python3
"""Syndication waterfall calculator with IRR hurdles.

Canonical runnable implementation of the corrected incremental-tier,
dated-cash-flow waterfall documented in references/advanced-analysis.md
(European-style / whole-fund). At each distribution date the cash required to
lift the investor IRR exactly to a hurdle equals the future value of the
investor's dated cash flows compounded at that hurdle rate; that amount —
grossed up by the tier's investor share — fills the tier before cash moves to
the next tier, so residual cash above a hurdle is split at the *next* tier's
promote, never at the lowest tier's split.

Also includes the simplified single-tier waterfall with GP catch-up
(``--mode simple``) for quick pref + promote splits of a single total.

Example invocation (the plugin's MCP venv has numpy and numpy-financial):
    PY=${CLAUDE_PLUGIN_ROOT}/mcp-servers/real-estate-data/.venv/bin/python
    $PY waterfall.py --sample-input > waterfall_inputs.json
    $PY waterfall.py --input waterfall_inputs.json --table
    $PY waterfall.py --mode simple --total-proceeds 15000000 \
        --lp-capital 10000000 --pref-rate 0.08 --promote 0.20

Requirements: numpy, numpy-financial
"""

import argparse
import json
import sys

import numpy as np
import numpy_financial as npf

SAMPLE_INPUT = {
    "lp_capital": 10000000,
    "gp_capital": 0,
    "annual_cash_flows": [0, 0, 0, 0, 15000000],
    "hurdles": [0.08, 0.12, 0.18],
    "lp_splits": [1.00, 0.80, 0.70],
    "residual_lp_split": 0.60,
}


def calculate_waterfall_irr(
    lp_capital,
    gp_capital,
    annual_cash_flows,
    hurdles=(0.08, 0.12, 0.18),
    lp_splits=(1.00, 0.80, 0.70),
    residual_lp_split=0.60,
):
    """European-style (whole-fund) distribution waterfall with IRR hurdles.

    Assumptions:
    - annual_cash_flows[t] is total distributable cash at the end of year t+1;
      all equity is invested at time 0 (annual periods, end-of-year flows).
    - Hurdles are investor IRR hurdles measured on the investor's dated cash
      flows (compound, cumulative pref — the first hurdle IS the pref rate).
    - GP co-investment (gp_capital), if any, is pari passu with LP capital:
      it earns its pro-rata share of every investor dollar. The GP promote
      (the 1 - split share of each tier) is on top of that.
    - lp_splits[i] is the investor share of tier cash until investor IRR
      reaches hurdles[i]; residual_lp_split applies above the last hurdle.
      Default: 100% to investors until 8% IRR, then 80/20 to 12%, 70/30 to
      18%, 60/40 thereafter.
    - No GP catch-up tier (see simple_waterfall for catch-up mechanics).

    Returns: dict with dated LP/GP cash flows, totals, and IRRs
    """
    n_years = len(annual_cash_flows)
    investor_capital = lp_capital + gp_capital

    # Dated flows: index 0 = time-0 investment, 1..N = year-end distributions
    investor_cf = np.zeros(n_years + 1)
    investor_cf[0] = -investor_capital
    promote_cf = np.zeros(n_years + 1)

    def cash_needed_to_reach(hurdle, year, flows):
        """Distribution at end of `year` that lifts the IRR of `flows` to
        exactly `hurdle`: the future value of the remaining shortfall,
        compounded at the hurdle rate."""
        fv = sum(flows[t] * (1 + hurdle) ** (year - t) for t in range(year + 1))
        return max(0.0, -fv)

    tier_hurdles = list(hurdles) + [None]          # None = uncapped residual
    tier_splits = list(lp_splits) + [residual_lp_split]

    for year in range(1, n_years + 1):
        remaining = annual_cash_flows[year - 1]
        for hurdle, inv_share in zip(tier_hurdles, tier_splits):
            if remaining <= 0:
                break
            if hurdle is None:
                tier_cash = remaining              # residual tier takes the rest
            else:
                inv_needed = cash_needed_to_reach(hurdle, year, investor_cf)
                if inv_needed <= 0:
                    continue                        # hurdle already met
                # Investors receive inv_share of each tier dollar
                tier_cash = min(remaining, inv_needed / inv_share)
            investor_cf[year] += tier_cash * inv_share
            promote_cf[year] += tier_cash * (1 - inv_share)
            remaining -= tier_cash

    # Attribute investor flows pro-rata; GP = co-invest share + 100% of promote
    lp_share = lp_capital / investor_capital
    lp_cf = investor_cf * lp_share
    gp_cf = investor_cf * (1 - lp_share) + promote_cf
    gp_cf[0] = -gp_capital

    project_cf = np.concatenate([[-investor_capital], annual_cash_flows])
    total_distributions = float(np.sum(annual_cash_flows))
    lp_total = float(np.sum(lp_cf[1:]))
    gp_total = float(np.sum(gp_cf[1:]))

    gp_irr = npf.irr(gp_cf) if gp_capital > 0 else None
    return {
        "project_irr": float(npf.irr(project_cf)),
        "lp_cash_flows": lp_cf.tolist(),
        "gp_cash_flows": gp_cf.tolist(),
        "lp_total": lp_total,
        "gp_total": gp_total,
        "lp_irr": float(npf.irr(lp_cf)),
        "gp_irr": None if gp_irr is None else float(gp_irr),
        "lp_percent": lp_total / total_distributions,
        "gp_percent": gp_total / total_distributions,
        "lp_equity_multiple": lp_total / lp_capital,
    }


def simple_waterfall(total_proceeds, lp_capital, pref_rate=0.08, promote=0.20):
    """Simplified single-distribution waterfall: return of capital, one year
    of pref, GP catch-up to the promote percentage, then a single promote
    split. Use for quick splits of one total; use calculate_waterfall_irr for
    dated multi-year cash flows."""
    distributions = {
        "lp": {"return_of_capital": 0.0, "pref_return": 0.0,
               "profit_split": 0.0, "total": 0.0},
        "gp": {"catchup": 0.0, "profit_split": 0.0, "total": 0.0},
    }

    remaining = total_proceeds

    # Tier 1: Return of capital
    distributions["lp"]["return_of_capital"] = min(lp_capital, remaining)
    remaining -= distributions["lp"]["return_of_capital"]

    if remaining > 0:
        # Tier 2: Preferred return
        pref_amount = lp_capital * pref_rate
        distributions["lp"]["pref_return"] = min(pref_amount, remaining)
        remaining -= distributions["lp"]["pref_return"]

    if remaining > 0:
        # Tier 3: GP catch-up (on pref only, so post-catch-up profit
        # above return of capital splits (1-promote)/promote)
        catchup_amount = (
            distributions["lp"]["pref_return"] * promote / (1 - promote)
        )
        distributions["gp"]["catchup"] = min(catchup_amount, remaining)
        remaining -= distributions["gp"]["catchup"]

    # Tier 4: Remaining split
    distributions["lp"]["profit_split"] = remaining * (1 - promote)
    distributions["gp"]["profit_split"] = remaining * promote

    distributions["lp"]["total"] = (
        distributions["lp"]["return_of_capital"]
        + distributions["lp"]["pref_return"]
        + distributions["lp"]["profit_split"]
    )
    distributions["gp"]["total"] = (
        distributions["gp"]["catchup"] + distributions["gp"]["profit_split"]
    )
    return distributions


def display_irr_summary(inputs, results, out=sys.stdout):
    w = out.write
    w("=" * 60 + "\n")
    w("WATERFALL SUMMARY (IRR-hurdle, whole-fund)\n")
    w("=" * 60 + "\n")
    w(f"LP capital:  ${inputs['lp_capital']:>14,.0f}\n")
    w(f"GP capital:  ${inputs['gp_capital']:>14,.0f}\n")
    hurdle_desc = ", ".join(
        f"{h:.0%} @ {s:.0%} LP" for h, s in zip(inputs["hurdles"], inputs["lp_splits"])
    )
    w(f"Tiers:       {hurdle_desc}, then {inputs['residual_lp_split']:.0%} LP\n\n")
    w(f"Project IRR: {results['project_irr']:.2%}\n")
    w(
        f"LP:  ${results['lp_total']:,.0f} ({results['lp_percent']:.1%} of "
        f"distributions), IRR {results['lp_irr']:.2%}, "
        f"{results['lp_equity_multiple']:.2f}x\n"
    )
    gp_irr = (
        f"{results['gp_irr']:.2%}" if results["gp_irr"] is not None
        else "n/a (no GP capital)"
    )
    w(
        f"GP:  ${results['gp_total']:,.0f} ({results['gp_percent']:.1%} of "
        f"distributions), IRR {gp_irr}\n\n"
    )
    w("Dated cash flows (year: LP / GP):\n")
    for year, (lp, gp) in enumerate(
        zip(results["lp_cash_flows"], results["gp_cash_flows"])
    ):
        w(f"  {year:>2}: {lp:>14,.0f} / {gp:>14,.0f}\n")


def display_simple_summary(result, out=sys.stdout):
    w = out.write
    w("=" * 60 + "\n")
    w("SIMPLE WATERFALL (pref + catch-up + single promote)\n")
    w("=" * 60 + "\n")
    w("LP distributions:\n")
    for key, value in result["lp"].items():
        w(f"  {key:<18} ${value:>14,.0f}\n")
    w("GP distributions:\n")
    for key, value in result["gp"].items():
        w(f"  {key:<18} ${value:>14,.0f}\n")
    total = result["lp"]["total"] + result["gp"]["total"]
    w(f"\nGP share of total: {result['gp']['total'] / total:.1%}\n")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Syndication waterfall calculator (JSON in / JSON or table out)."
    )
    parser.add_argument(
        "--mode",
        choices=["irr", "simple"],
        default="irr",
        help="'irr': dated cash flows through IRR hurdles (default); "
        "'simple': single total through pref + catch-up + one promote tier",
    )
    parser.add_argument(
        "--input",
        help="Path to JSON input file (use '-' for stdin). Keys for irr mode: "
        "lp_capital, gp_capital, annual_cash_flows, hurdles, lp_splits, "
        "residual_lp_split",
    )
    parser.add_argument("--output", help="Write results JSON to this path")
    parser.add_argument(
        "--table", action="store_true",
        help="Print a human-readable summary instead of JSON",
    )
    parser.add_argument(
        "--sample-input", action="store_true",
        help="Print a sample irr-mode input JSON document and exit",
    )
    # simple-mode flags (may also be given via --input JSON)
    parser.add_argument("--total-proceeds", type=float)
    parser.add_argument("--lp-capital", type=float)
    parser.add_argument("--pref-rate", type=float, default=0.08)
    parser.add_argument("--promote", type=float, default=0.20)
    args = parser.parse_args(argv)

    if args.sample_input:
        json.dump(SAMPLE_INPUT, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    params = {}
    if args.input:
        if args.input == "-":
            params = json.load(sys.stdin)
        else:
            with open(args.input) as f:
                params = json.load(f)

    if args.mode == "simple":
        total_proceeds = args.total_proceeds or params.get("total_proceeds")
        lp_capital = args.lp_capital or params.get("lp_capital")
        if total_proceeds is None or lp_capital is None:
            parser.error(
                "simple mode needs --total-proceeds and --lp-capital "
                "(flags or JSON keys)"
            )
        result = simple_waterfall(
            total_proceeds,
            lp_capital,
            params.get("pref_rate", args.pref_rate),
            params.get("promote", args.promote),
        )
        payload = {"inputs": {
            "total_proceeds": total_proceeds, "lp_capital": lp_capital,
            "pref_rate": params.get("pref_rate", args.pref_rate),
            "promote": params.get("promote", args.promote),
        }, "distributions": result}
        if args.table:
            display_simple_summary(result)
    else:
        if not params:
            parser.error("--input is required for irr mode (or use --sample-input)")
        inputs = {
            "lp_capital": params["lp_capital"],
            "gp_capital": params.get("gp_capital", 0),
            "annual_cash_flows": params["annual_cash_flows"],
            "hurdles": params.get("hurdles", [0.08, 0.12, 0.18]),
            "lp_splits": params.get("lp_splits", [1.00, 0.80, 0.70]),
            "residual_lp_split": params.get("residual_lp_split", 0.60),
        }
        results = calculate_waterfall_irr(**inputs)
        payload = {"inputs": inputs, "results": results}
        if args.table:
            display_irr_summary(inputs, results)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(payload, f, indent=2)
        sys.stderr.write(f"Wrote results to {args.output}\n")
    elif not args.table:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
