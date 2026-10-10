---
description: Create or update portfolio.json in the working directory (add, update, remove properties), then review the portfolio with the portfolio-reviewer agent
argument-hint: "[add|update|remove|review] [property details]"
---

# Portfolio Tracker and Review

Request: $ARGUMENTS

`portfolio.json` in the user's working directory is this plugin's record of their holdings; `/exit-analysis` and the portfolio-reviewer agent read it. Its fields are documented in the `_schema` block of `${CLAUDE_PLUGIN_ROOT}/templates/portfolio-template.json`.

## 1. Find or create the file

Look for `portfolio.json` in the working directory.

- **Found**: read it and show a one-line summary (property count, total value, `as_of` date). If `as_of` is more than six months old, say the figures may be stale, and continue.
- **Missing**: create it from the template: keep the `_schema` block, replace the example properties with the user's, and set `as_of` to today. If the user hasn't given any properties yet, ask for the first one with an example: `/portfolio add 12 Oak St, SFR, bought 2019 for $310k, owe $224k at 3.75% to 2049, rent $2,450, NOI $17,600, worth ~$415k`.

## 2. Apply the change

- **add**: required fields are `property`, `basis`, `debt` (with `rate` and `maturity` if above 0), `rent`, `noi` and `value`. Ask once for whichever are missing. Recommended: `type`, `acquired`, `accumulated_depreciation`, `value_source`; optional: `cost_seg_depreciation`, `annual_debt_service` (important for interest-only or balloon loans), `amortization_years`, `notes`.
- **update**: find the entry by address (a close match is fine; say which one you matched), change the named fields, refresh `as_of`.
- **remove**: confirm, then delete the entry. If they're selling rather than tidying up, suggest `/exit-analysis` first.
- **review**, or no action: go to step 4.

Before writing: amounts are plain numbers, rates are decimals (0.065, not 6.5), dates are YYYY-MM-DD, and warn (don't block) if debt exceeds value. Keep the `_schema` block and every field you didn't change. Write only to the working directory's `portfolio.json`.

## 3. Show what was written

One line per property (address, value, debt, NOI, rate, maturity) so the user can spot typos.

## 4. Review

Run the **portfolio-reviewer** agent and tell it to read `portfolio.json` in the working directory. It reports aggregate leverage, NOI, cash flow and DSCR, concentration and refinance risk, a property ranking, and recommended moves.

## 5. Next steps

Offer what fits the review: `/exit-analysis <address>` for disposition or refinance candidates, `/analyze-deal` for an acquisition the review suggests, and `/portfolio update` when values, rents or balances change.
