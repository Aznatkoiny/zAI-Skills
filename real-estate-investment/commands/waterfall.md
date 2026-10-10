---
description: Syndication waterfall calculator — LP/GP distributions through IRR hurdles (or a simple pref + catch-up), run with the plugin's tested script
argument-hint: "[american|european] [equity, hurdles, cash flows]"
---

# Syndication Waterfall Calculator

Request: $ARGUMENTS

Model the waterfall by running the plugin's tested script rather than writing the tier math from prose. Mechanics, American vs. European, and the script's assumptions: `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/references/advanced-analysis.md` §Waterfall.

## 1. Inputs

Needed: **LP equity** (and any GP co-investment) and the **distributable cash flows** by year, including sale proceeds in the final year. If cash flows aren't given, derive them from a hold period, a target equity multiple and a distribution pattern ("all at exit" or "X% a year plus exit"), or reuse a pro forma's net cash flows and sale proceeds if one was just run.

Hurdles and splits default to the plugin's typical structure (the script's defaults): 100% to LPs until an 8% IRR, 80/20 to 12%, 70/30 to 18%, 60/40 above. Use the user's operating-agreement terms when they give them.

If the request is empty, ask for equity and cash flows with an example: `/waterfall $10M LP, $500k GP, distributions $600k/yr for 4 years then $14M at exit`.

**Type**: the script implements European (whole-fund) hurdles on dated cash flows. For American (deal-by-deal), run it once per deal with that deal's equity and cash flows and sum the GP promote.

## 2. Run

```bash
PY="${CLAUDE_PLUGIN_ROOT}/mcp-servers/real-estate-data/.venv/bin/python"
S="${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts"
"$PY" "$S/waterfall.py" --sample-input            # schema
# write waterfall_inputs.json (lp_capital, gp_capital, annual_cash_flows,
# hurdles, lp_splits, residual_lp_split), then:
"$PY" "$S/waterfall.py" --input waterfall_inputs.json --output waterfall_results.json
"$PY" "$S/waterfall.py" --input waterfall_inputs.json --table
```

For a single total split with a pref and full GP catch-up (no dated flows):

```bash
"$PY" "$S/waterfall.py" --mode simple --total-proceeds 15000000 \
    --lp-capital 10000000 --pref-rate 0.08 --promote 0.20 --table
```

If that Python is missing, see `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/SKILL.md` §Running the Scripts; ask before installing anything.

## 3. Present

| | LP | GP |
|---|---|---|
| Equity invested | | |
| Cash distributed | | |
| Share of distributions | | |
| IRR | | |

Plus project IRR, LP equity multiple, and the LP/GP cash flows by year. Split GP economics into co-investment return and promote (promote = GP total − the GP's pro-rata investor share). Management fees (often 1-2% of equity a year) aren't in the script; add them separately if they apply.

**Scenarios**: re-run with cash flows scaled to roughly a 1.5× and a 2.5× gross equity multiple next to the base case, and show LP IRR, GP promote dollars and GP share of distributions for each. The promote share rises steeply with performance, which is the point of the structure.

## Notes

- IRR mode has no GP catch-up tier; `--mode simple` does. If the agreement has both a catch-up and IRR hurdles, say how the script's result differs.
- Point out whether the GP has real money in the deal or only the promote, and flag structures that give the GP more than 30% at early hurdles.
- The GP promote is carried interest: under §1061 it needs a 3-year holding period for long-term capital gain treatment, though gain from selling rental property (§1231) is generally excluded. A CPA should confirm.
