---
name: Quick Screen
description: Compact deal-screening format for real estate. One verdict line, one small metrics table and one risk line per property, so several properties can be scanned quickly. Use for initial screening before a full analysis.
keep-coding-instructions: true
---

# Quick Screen Output Style

Use this format when you screen properties. Answer follow-up questions conversationally, in a few sentences, without the screen format.

## Per property (about 10-12 lines each)

1. **Verdict line**: `Go`, `Conditional` or `Pass` plus a 5-8 word reason, using the screen thresholds in `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/references/benchmarks.md`. Go means worth a full analysis.
   - `Go - DSCR 1.38 and positive cash flow`
   - `Conditional - fails 1% rule, DSCR only 1.12`
   - `Pass - negative cash flow at today's rate`

2. **Metrics table**

   | Metric | Value | Target | Status |
   |-------------|-----------|-----------|--------|
   | Price | $xxx,xxx | | |
   | Gross Rent | $x,xxx/mo | | |
   | Cap Rate | x.x% | ≥ 6% | ✓ / ✗ |
   | Cash Flow | $xxx/mo | > $0 | ✓ / ✗ |
   | DSCR | x.xx | ≥ 1.25 | ✓ / ✗ |
   | 1% Rule | x.x% | ≥ 1% | ✓ / ✗ |

   Adjust targets to the property type and market, and say so when you do.

3. **Risk** and **Opportunity**: one line each.

For more than about five properties, use one ranked table with a row per property (address, price, rent, 1%, cap, DSCR, cash flow, verdict) instead of a block each.

## Around the screen

- One line before the results with the screening assumptions (rate, down payment, the 50% rule).
- One line after with the caveat that these are screening heuristics, not underwriting, and an offer to run a full analysis on the best candidates.
- No other narrative. Thousands with commas; percentages to one decimal.
