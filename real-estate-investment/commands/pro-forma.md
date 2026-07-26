---
description: Run the canonical pro forma script on a property — metrics, cash flow table, and JSON results (Excel formulas optional)
argument-hint: "[python|excel|both]"
---

# Generate Pro Forma Model

Requested output format (may be empty): $ARGUMENTS

## Instructions

When this command is invoked, build a real estate pro forma by **running the plugin's tested script** — do not re-write the model from prose:

### 1. Collect Property Details

Use AskUserQuestion to gather (these map 1:1 to the script's input schema):

- **Property type**: SFR, multifamily, commercial, STR
- **Purchase price**
- **Income**: units and annual rent per unit (or a single `annual_gross_rent`), other income % of rent (default 3%), vacancy rate
- **Operating expenses**: OpEx ratio as % of EGI (benchmarks: 35-45% multifamily, 40-50% commercial, 50-60% STR)
- **Financing**: LTV (if the user gives a down payment %, `ltv = 1 - down_payment_pct`), annual interest rate, amortization years
- **Assumptions**: holding period (default 10), rent growth (default 3%), expense growth (default 2.5%), CapEx reserve % of EGI (default 5%), exit cap rate, selling costs % (default 3%)

### 2. Validate Assumptions with Market Data (optional but recommended)

If the user has a specific property address, ground the model's assumptions using the `real-estate-data` MCP server (tools surface as `mcp__real-estate-data__<name>`):

- `mcp__real-estate-data__estimate_rent` — replace guessed rent with a Rentcast AVM estimate (requires `RENTCAST_API_KEY`; free tier, 50 requests/month)
- `mcp__real-estate-data__get_rentcast_market_data` — ZIP-level vacancy rate and rent growth for the income assumptions (requires `RENTCAST_API_KEY`)
- `mcp__real-estate-data__get_attom_property` — year built, building size, beds/baths for expense benchmarking (requires `ATTOM_API_KEY`, paid)
- `mcp__real-estate-data__get_attom_valuation` — AVM check on the purchase price (requires `ATTOM_API_KEY`, paid)
- `mcp__real-estate-data__get_census_housing_stats` — area median home value context (requires `CENSUS_API_KEY` — the key is free to obtain)

**Fallback chain:** MCP tool → WebSearch for comparable data → use the user's manual inputs as-is. Note in the results which inputs are data-backed vs. assumed.

### 3. Write the Input File and Run the Script

The canonical model is `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/pro_forma.py`. Print its schema template, write the user's parameters into `pro_forma_inputs.json` in the working directory, then run it via Bash:

```bash
# Schema template (property / loan / assumptions keys):
python "${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/pro_forma.py" --sample-input

# After writing pro_forma_inputs.json with the user's numbers:
python "${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/pro_forma.py" \
    --input pro_forma_inputs.json --output pro_forma_results.json
python "${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/pro_forma.py" \
    --input pro_forma_inputs.json --table
```

If the imports fail, install the two dependencies first (`pip install numpy numpy-financial`, or into a project venv if the user prefers).

### 4. Present Results

Relay the script's summary: purchase cap rate, year-1 cash-on-cash, year-1 DSCR, levered IRR, equity multiple, NPV @ 8/10/12%, and the year-by-year cash flow table. Flag red flags (DSCR < 1.2x, negative cash flow years, IRR below the user's hurdle).

Offer a price × rate stress grid on the same input file:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/sensitivity.py" \
    --input pro_forma_inputs.json
```

### 5. Generate Excel Formulas (if "excel" or "both" requested)

Read `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/references/financial-metrics.md` (§Excel Reference) and create a cell-by-cell layout saved as `pro_forma_formulas.txt`:

- **Input sheet**: all assumptions in named cells
- **Pro forma sheet**: Year 0 acquisition, Years 1-N operations, exit year — GPR growth `=Base*(1+g)^(N-1)`, vacancy, EGI, OpEx escalation, NOI, `=PMT()` debt service, cash flow, `=IRR()`/`=XIRR()` returns
- Include the NPV timing caveat (`=NPV(rate, B3:B12) + B2`) and the amortization sign convention from the reference

### 6. Deliver Files

Confirm what was written to the working directory: `pro_forma_inputs.json` (editable assumptions), `pro_forma_results.json` (full projection + metrics), and `pro_forma_formulas.txt` if Excel output was requested. If the user wants to customize the model logic itself, copy `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/scripts/pro_forma.py` into their project and edit the copy — never edit the plugin's copy.

## Notes

- The script's expense handling is the corrected version: Year-1 OpEx = Year-1 EGI × opex_ratio, then escalated at `expense_growth` only — do not "fix" it to re-derive OpEx from grown revenue
- For STR properties, convert ADR × occupancy × 365 into `annual_gross_rent` and use an STR OpEx ratio (50-65%)
- For multifamily, use per-unit inputs (`units` × `annual_rent_per_unit`)
- To iterate on assumptions, edit `pro_forma_inputs.json` and re-run — that is the whole point of the JSON-in/JSON-out design
