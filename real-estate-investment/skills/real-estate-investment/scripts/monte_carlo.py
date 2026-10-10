#!/usr/bin/env python3
"""Monte Carlo simulation for real estate returns.

Canonical runnable implementation of the Monte Carlo framework documented in
references/advanced-analysis.md. Randomizes rent growth (normal), vacancy
(normal, clipped), and exit cap rate (triangular) over an unlevered NOI
projection with a terminal sale, then reports the IRR/NPV distribution:
mean, median, standard deviation, 5th/95th percentiles, value-at-risk,
probability of loss, and probability of clearing target IRRs.

Example invocation (the plugin's MCP venv has numpy and numpy-financial):
    PY=${CLAUDE_PLUGIN_ROOT}/mcp-servers/real-estate-data/.venv/bin/python
    $PY monte_carlo.py --sample-input > mc_inputs.json
    $PY monte_carlo.py --input mc_inputs.json --table
    $PY monte_carlo.py --input mc_inputs.json --simulations 20000 --seed 42

Requirements: numpy, numpy-financial
"""

import argparse
import json
import sys

import numpy as np
import numpy_financial as npf

SAMPLE_INPUT = {
    "purchase_price": 50000000,
    "year_1_noi_at_full_occupancy": 3500000,
    "hold_period": 5,
    "rent_growth": {"mean": 0.03, "std": 0.02, "min": -0.05, "max": 0.15},
    "vacancy": {"mean": 0.08, "std": 0.03, "min": 0.02, "max": 0.30},
    "exit_cap": {"min": 0.045, "mode": 0.055, "max": 0.070},
    "discount_rate": 0.10,
    "target_irrs": [0.08, 0.10, 0.12, 0.15],
}


def run_simulation(params, n_simulations=10000, seed=None):
    """Run the Monte Carlo simulation; returns (irr_array, npv_array).

    Model per draw: Year-1 NOI = year_1_noi_at_full_occupancy * (1 - vacancy);
    NOI grows at the drawn rent-growth rate; terminal value = Year-(N+1) NOI /
    drawn exit cap, added to the final-year flow; IRR/NPV on the unlevered
    cash flow vector [-purchase_price, NOI_1, ..., NOI_N + terminal].
    """
    rng = np.random.default_rng(seed)
    hold = params["hold_period"]
    price = params["purchase_price"]
    base_noi = params["year_1_noi_at_full_occupancy"]
    rg, vac, cap = params["rent_growth"], params["vacancy"], params["exit_cap"]

    irr_results = np.empty(n_simulations)
    npv_results = np.empty(n_simulations)

    for i in range(n_simulations):
        rent_growth = np.clip(
            rng.normal(rg["mean"], rg["std"]), rg.get("min", -0.05), rg.get("max", 0.15)
        )
        vacancy = np.clip(
            rng.normal(vac["mean"], vac["std"]), vac.get("min", 0.0), vac.get("max", 1.0)
        )
        exit_cap = rng.triangular(cap["min"], cap["mode"], cap["max"])

        year_1_noi = base_noi * (1 - vacancy)
        cash_flows = [-price]
        for year in range(1, hold + 1):
            cash_flows.append(year_1_noi * (1 + rent_growth) ** (year - 1))
        terminal_noi = cash_flows[-1] * (1 + rent_growth)
        cash_flows[-1] += terminal_noi / exit_cap

        irr_results[i] = npf.irr(cash_flows)
        npv_results[i] = npf.npv(params.get("discount_rate", 0.10), cash_flows)

    return irr_results, npv_results


def summarize(params, irr_results, npv_results, n_simulations, seed):
    valid_irr = irr_results[~np.isnan(irr_results)]
    targets = params.get("target_irrs", [0.08, 0.10, 0.12, 0.15])
    return {
        "simulations": n_simulations,
        "seed": seed,
        "irr": {
            "mean": float(np.mean(valid_irr)),
            "median": float(np.median(valid_irr)),
            "std": float(np.std(valid_irr)),
            "p5": float(np.percentile(valid_irr, 5)),
            "p95": float(np.percentile(valid_irr, 95)),
        },
        "npv": {
            "mean": float(np.mean(npv_results)),
            "median": float(np.median(npv_results)),
            "std": float(np.std(npv_results)),
            "p5": float(np.percentile(npv_results, 5)),
            "p95": float(np.percentile(npv_results, 95)),
        },
        "var_5pct_npv": float(np.percentile(npv_results, 5)),
        "prob_npv_below_zero": float(np.mean(npv_results < 0)),
        "prob_irr_at_or_above": {
            f"{t:.0%}": float(np.mean(valid_irr >= t)) for t in targets
        },
    }


def display_summary(stats, out=sys.stdout):
    w = out.write
    w("=" * 60 + "\n")
    w("MONTE CARLO SIMULATION RESULTS\n")
    w("=" * 60 + "\n")
    w(f"Simulations: {stats['simulations']:,}")
    w(f"  (seed: {stats['seed']})\n" if stats["seed"] is not None else "\n")
    w("\nIRR distribution (unlevered):\n")
    w(f"  Mean:            {stats['irr']['mean']:>8.2%}\n")
    w(f"  Median:          {stats['irr']['median']:>8.2%}\n")
    w(f"  Std Dev:         {stats['irr']['std']:>8.2%}\n")
    w(f"  5th percentile:  {stats['irr']['p5']:>8.2%}\n")
    w(f"  95th percentile: {stats['irr']['p95']:>8.2%}\n")
    w("\nNPV distribution:\n")
    w(f"  Mean:            ${stats['npv']['mean']:>14,.0f}\n")
    w(f"  5th percentile:  ${stats['npv']['p5']:>14,.0f}\n")
    w(f"  95th percentile: ${stats['npv']['p95']:>14,.0f}\n")
    w(f"\n5% VaR (NPV):      ${stats['var_5pct_npv']:>14,.0f}\n")
    w(f"P(NPV < 0):        {stats['prob_npv_below_zero']:>8.1%}\n")
    w("\nTarget IRR probabilities:\n")
    for target, prob in stats["prob_irr_at_or_above"].items():
        w(f"  P(IRR >= {target:>4}): {prob:>7.1%}\n")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Monte Carlo real estate return simulation "
        "(JSON in / JSON or table out)."
    )
    parser.add_argument(
        "--input",
        help="Path to JSON input file (use '-' for stdin); "
        "see --sample-input for the expected keys",
    )
    parser.add_argument("--output", help="Write results JSON to this path")
    parser.add_argument(
        "--simulations", type=int, default=10000,
        help="Number of simulation draws (default: 10000)",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducible results",
    )
    parser.add_argument(
        "--table", action="store_true",
        help="Print a human-readable summary instead of JSON",
    )
    parser.add_argument(
        "--sample-input", action="store_true",
        help="Print a sample input JSON document and exit",
    )
    args = parser.parse_args(argv)

    if args.sample_input:
        json.dump(SAMPLE_INPUT, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if not args.input:
        parser.error("--input is required (or use --sample-input)")

    if args.input == "-":
        params = json.load(sys.stdin)
    else:
        with open(args.input) as f:
            params = json.load(f)

    irr_results, npv_results = run_simulation(params, args.simulations, args.seed)
    stats = summarize(params, irr_results, npv_results, args.simulations, args.seed)
    payload = {"inputs": params, "results": stats}

    if args.output:
        with open(args.output, "w") as f:
            json.dump(payload, f, indent=2)
        sys.stderr.write(f"Wrote results to {args.output}\n")

    if args.table:
        display_summary(stats)
    elif not args.output:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
