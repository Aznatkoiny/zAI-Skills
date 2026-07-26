---
description: Syndication waterfall distribution calculator — model GP/LP profit splits across IRR hurdles
argument-hint: "[american|european]"
---

# Syndication Waterfall Calculator

Requested waterfall type (may be empty): $ARGUMENTS

## Instructions

When this command is invoked, model a real estate syndication waterfall by **running the plugin's tested script** — do not re-write the tier math from prose:

### 1. Load Reference Material

Read `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/references/advanced-analysis.md` (§3 Waterfall Distribution Modeling) for tier structures, catch-up mechanics, American vs. European differences, and the script's documented assumptions.

### 2. Collect Syndication Structure

Use AskUserQuestion to gather:

**Equity Structure:**
- LP equity contribution (typically 90-95% of total)
- GP equity co-investment (dollar amount or %; may be zero)

**Hurdles and Splits:**
- Preferred return rate (annual %, typical: 6-8%) — in the script this is the **first IRR hurdle** (compound, cumulative)
- IRR hurdle schedule and LP share per tier, e.g. 100% LP to 8%, 80/20 to 12%, 70/30 to 18%, 60/40 above (the script's defaults)
- Residual LP split above the highest hurdle

**Waterfall Type (skip if provided via $ARGUMENTS):**
- **European (whole-fund)**: hurdles measured on aggregate dated cash flows — this is what the script implements directly
- **American (deal-by-deal)**: run the script once per deal, each with its own equity and cash flow vector, then sum GP promote across deals

### 3. Collect Cash Flow Projections

Ask for the annual distributable cash flows (end-of-year, Years 1-N), including exit proceeds in the final year. Alternatively, derive them from a hold period + target equity multiple + distribution pattern (e.g., "all at exit" or "X% annually plus exit"). If a pro forma was already built with `/pro-forma`, reuse its net cash flows and sale proceeds.

### 4. Run the Canonical Script

The tested implementation is `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/waterfall.py`. Write the structure into `waterfall_inputs.json` and run via Bash:

```bash
# Schema template:
python "${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/waterfall.py" --sample-input

# After writing waterfall_inputs.json (lp_capital, gp_capital,
# annual_cash_flows, hurdles, lp_splits, residual_lp_split):
python "${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/waterfall.py" \
    --input waterfall_inputs.json --output waterfall_results.json
python "${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/waterfall.py" \
    --input waterfall_inputs.json --table
```

If the imports fail, install the dependencies first (`pip install numpy numpy-financial`).

For a quick single-distribution split with GP catch-up (no dated flows), use simple mode instead:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/waterfall.py" \
    --mode simple --total-proceeds 15000000 --lp-capital 10000000 \
    --pref-rate 0.08 --promote 0.20 --table
```

### 5. Present the Waterfall Breakdown

From `waterfall_results.json`, present:

**Return Summary:**
| Metric | LP | GP |
|--------|----|----|
| Equity Invested | | |
| Cash Distributed | | |
| Share of Distributions | | |
| IRR | | |

Plus project IRR, LP equity multiple, and the dated LP/GP cash flow vectors. Break GP economics into co-investment return vs. promote (the script reports GP totals; promote = GP total minus the GP's pro-rata investor share). Add management fees separately if applicable (typical: 1-2% of equity per year — not modeled by the script).

### 6. Sensitivity Scenarios

Re-run the script with scaled cash flow vectors to show how the split shifts:
- **Downside**: ~1.5x gross multiple
- **Base**: user inputs
- **Upside**: ~2.5x gross multiple

For each scenario report LP IRR, GP promote dollars, and GP % of distributions. (Promote share rises steeply with performance — that is the point of the structure.)

## Notes

- Explain American vs. European clearly; the script is whole-fund — model American deals per-deal as described above
- The script has **no GP catch-up tier** in IRR mode; catch-up exists in `--mode simple`. If the user's operating agreement has a catch-up plus IRR hurdles, say so explicitly and adjust interpretation
- Highlight GP alignment: does the GP invest equity, or only receive promote?
- Flag aggressive structures (GP >30% at early hurdles)
- Note tax treatment: GP promote is typically taxed as long-term capital gains (carried interest)
