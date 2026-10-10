#!/usr/bin/env python3
"""Two-way sensitivity grid (purchase price x interest rate) for a pro forma.

Runs the canonical RealEstateProForma model (scripts/pro_forma.py) across a
grid of purchase prices and loan interest rates, holding every other
assumption constant, and prints a markdown table of the chosen metric
(levered IRR by default; also year-1 cash-on-cash or year-1 DSCR).
The input file uses the same JSON schema as pro_forma.py.

Example invocation (the plugin's MCP venv has numpy and numpy-financial):
    PY=${CLAUDE_PLUGIN_ROOT}/mcp-servers/real-estate-data/.venv/bin/python
    $PY pro_forma.py --sample-input > inputs.json
    $PY sensitivity.py --input inputs.json
    $PY sensitivity.py --input inputs.json --metric coc \
        --price-spread 0.15 --rate-spread 0.015 --steps 7

Requirements: numpy, numpy-financial
"""

import argparse
import copy
import json
import math
import sys

import numpy as np

from pro_forma import RealEstateProForma

METRIC_KEYS = {
    "irr": ("irr", "Levered IRR"),
    "coc": ("year_1_cash_on_cash", "Year-1 Cash-on-Cash"),
    "dscr": ("year_1_dscr", "Year-1 DSCR"),
}


def run_grid(params, prices, rates, metric="irr"):
    """Return a 2D list (rows=prices, cols=rates) of the metric value.

    Cells where the model cannot solve (e.g., IRR undefined because every
    cash flow is negative) come back as NaN.
    """
    key = METRIC_KEYS[metric][0]
    grid = []
    for price in prices:
        row = []
        for rate in rates:
            scenario = copy.deepcopy(params)
            scenario["property"]["purchase_price"] = float(price)
            scenario["loan"]["interest_rate"] = float(rate)
            try:
                model = RealEstateProForma(
                    scenario["property"], scenario["loan"], scenario["assumptions"]
                )
                value = float(model.calculate_metrics()[key])
            except Exception:
                value = float("nan")
            row.append(value)
        grid.append(row)
    return grid


def format_markdown(prices, rates, grid, metric, base_price, base_rate):
    """Render the grid as a markdown table (prices as rows, rates as columns)."""
    label = METRIC_KEYS[metric][1]

    def cell(value):
        if math.isnan(value):
            return "n/a"
        return f"{value:.2f}x" if metric == "dscr" else f"{value:.1%}"

    lines = [
        f"**{label} — purchase price (rows) x interest rate (columns)**",
        "",
        "| Price \\ Rate | "
        + " | ".join(f"{r:.2%}" for r in rates)
        + " |",
        "|---" * (len(rates) + 1) + "|",
    ]
    for price, row in zip(prices, grid):
        marker = " (base)" if math.isclose(price, base_price) else ""
        lines.append(
            f"| ${price:,.0f}{marker} | " + " | ".join(cell(v) for v in row) + " |"
        )
    lines.append("")
    lines.append(
        f"Base case: ${base_price:,.0f} at {base_rate:.2%}. "
        "All other assumptions held constant."
    )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Price x rate sensitivity grid on the pro forma model "
        "(markdown table out)."
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to pro_forma.py-style JSON input file (use '-' for stdin)",
    )
    parser.add_argument(
        "--metric", choices=sorted(METRIC_KEYS), default="irr",
        help="Metric to tabulate: irr (default), coc, or dscr",
    )
    parser.add_argument(
        "--price-spread", type=float, default=0.10,
        help="Fractional spread around the base price (default 0.10 = +/-10%%)",
    )
    parser.add_argument(
        "--rate-spread", type=float, default=0.01,
        help="Absolute spread around the base rate (default 0.01 = +/-100 bps)",
    )
    parser.add_argument(
        "--steps", type=int, default=5,
        help="Grid points per axis (default 5; use odd numbers to keep the "
        "base case on the grid)",
    )
    parser.add_argument("--output", help="Write the markdown table to this path")
    args = parser.parse_args(argv)

    if args.steps < 2:
        parser.error("--steps must be at least 2")

    if args.input == "-":
        params = json.load(sys.stdin)
    else:
        with open(args.input) as f:
            params = json.load(f)

    base_price = params["property"]["purchase_price"]
    base_rate = params["loan"]["interest_rate"]
    prices = np.linspace(
        base_price * (1 - args.price_spread),
        base_price * (1 + args.price_spread),
        args.steps,
    )
    rates = np.linspace(
        base_rate - args.rate_spread, base_rate + args.rate_spread, args.steps
    )

    grid = run_grid(params, prices, rates, args.metric)
    table = format_markdown(prices, rates, grid, args.metric, base_price, base_rate)

    if args.output:
        with open(args.output, "w") as f:
            f.write(table + "\n")
        sys.stderr.write(f"Wrote table to {args.output}\n")
    else:
        print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
