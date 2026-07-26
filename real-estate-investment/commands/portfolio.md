---
description: Create or update portfolio.json in the working directory, then run the portfolio-reviewer agent against it
argument-hint: "[add|update|remove|review] [property details]"
---

# Portfolio Tracker & Review

Requested action and details (may be empty): $ARGUMENTS

## Instructions

When this command is invoked, maintain the user's persistent portfolio file and review it:

### 1. Locate or Create portfolio.json

Look for `portfolio.json` in the current working directory (Glob/Read).

- **Exists**: Read it and confirm the property count and `as_of` date with the user
- **Missing**: create it from the plugin template — Read `${CLAUDE_PLUGIN_ROOT}/templates/portfolio-template.json`, keep its `_schema` block, replace the example entries with the user's actual properties, and set `as_of` to today

### 2. Apply the Requested Change

Interpret $ARGUMENTS (or ask):

- **add**: collect the schema fields for the new property via AskUserQuestion — required: `property`, `basis`, `debt`, `rate` + `maturity` (if debt > 0), `rent`, `noi`, `value`; recommended: `type`, `acquired`, `accumulated_depreciation`, `value_source`, `notes`
- **update**: locate the entry by address (fuzzy match is fine, confirm the match), update the named fields, refresh `as_of`
- **remove**: delete the entry after confirmation (suggest `/exit-analysis` first if they are selling rather than just cleaning up)
- **review** (or no action given): skip straight to step 4

Validate before writing: numbers are plain numbers, rates are decimals (0.065 not 6.5), dates are YYYY-MM-DD, `debt <= value` sanity check (warn, don't block). Write the updated file with Write, preserving the `_schema` block and any fields you did not touch.

### 3. Confirm the Write

Show a one-line-per-property summary table (address, value, debt, NOI, rate, maturity) so the user can spot typos before analysis runs.

### 4. Run the Portfolio Review

Invoke the **portfolio-reviewer** agent, telling it to read `portfolio.json` in the working directory as its data source. It aggregates portfolio metrics (LTV, weighted cap rate, portfolio DSCR, CoC), flags concentration and refinance risks, ranks property performance, and recommends optimization moves.

### 5. Follow-Ups

Based on the review, offer the natural next commands:

- `/exit-analysis <address>` for any property flagged as a disposition or refi candidate
- `/analyze-deal` if the review recommends acquiring in a gap market
- Re-run `/portfolio update` whenever values, rents, or balances change materially

## Notes

- `portfolio.json` lives in the **user's working directory**, not the plugin — it is the persistence layer for this plugin's portfolio features and is safe to commit to a private repo
- Never write user portfolio data anywhere except the working directory's `portfolio.json`
- Schema documentation lives in the template's `_schema` block: `${CLAUDE_PLUGIN_ROOT}/templates/portfolio-template.json`
