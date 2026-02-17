---
description: Generate a real estate pro forma model in Python or Excel format
---

# Generate Pro Forma Model

ARGUMENTS: Optional output format ("python", "excel", or "both")

## Instructions

When this command is invoked, generate a complete real estate pro forma financial model:

### 1. Collect Property Details

Use AskUserQuestion to gather:
- **Property type**: SFR, multifamily, commercial, STR
- **Purchase price and acquisition costs**
- **Financing terms**: Down payment, interest rate, loan term, amortization
- **Income assumptions**: Monthly rent, vacancy rate, other income, annual growth rate
- **Operating expenses**: Property taxes, insurance, maintenance, management, utilities, etc.
- **Holding period**: Number of years (default: 10)
- **Exit assumptions**: Exit cap rate, selling costs

### 2. Collect Output Preference

Ask for output format (skip if provided via ARGUMENTS):
- Python script
- Excel formulas
- Both

### 3. Load Reference Material

Read the financial metrics reference:
the `references/financial-metrics.md` file from the `real-estate-investment` skill in this plugin

### 4. Generate Python Script (if requested)

Create a complete Python pro forma model using the RealEstateProForma class pattern from the reference:

**Include:**
- Property class with all input parameters
- Income schedule calculation (gross rent, vacancy, effective gross income)
- Expense schedule (all operating expenses with inflation)
- Debt service calculation (monthly P&I using amortization formula)
- Cash flow waterfall (EGI - OpEx - Debt Service = Cash Flow)
- Return metrics calculation (Cap Rate, CoC, IRR, Equity Multiple, DSCR)
- Exit/reversion value calculation
- Output methods for annual projections and summary metrics

**Output:**
- Save as `pro_forma.py` in working directory
- Include clear comments and docstrings
- Add example usage at the bottom

### 5. Generate Excel Formulas (if requested)

Create cell-by-cell Excel layout with formulas:

**Structure:**
- **Input Sheet**: All assumptions in named cells
- **Pro Forma Sheet**: 10-year (or custom) projection with rows for:
  - Year 0 (acquisition)
  - Years 1-N (operations)
  - Year N+1 (exit/sale)

**Provide formulas for:**
- Gross Potential Rent: `=B3*(1+$C$5)^A10` (where B3=Year 1 rent, C5=growth rate, A10=year)
- Vacancy Loss: `=B10*$C$6` (where C6=vacancy rate)
- Effective Gross Income: `=B10-C10`
- Operating Expenses: Individual line items with inflation
- NOI: `=EGI-Total OpEx`
- Debt Service: `=PMT($C$8,$C$9,-$C$7)` (rate, periods, loan amount)
- Cash Flow: `=NOI-DebtService`
- Cumulative Cash Flow: `=SUM($H$10:H10)`
- IRR: `=XIRR(CashFlows, Dates)`

**Output:**
- Save as `pro_forma_formulas.txt` with clear layout instructions
- Include named range definitions

### 6. Generate Both (if requested)

Create both Python script and Excel formula layout.

### 7. Verify and Save

Save generated file(s) to the user's working directory and confirm:
- File name(s) and location
- Brief usage instructions
- Note that user can customize inputs directly in the file(s)

## Notes

- For STR properties, include seasonal occupancy/ADR modeling
- For multifamily, support per-unit input with vacancy loss by unit type
- Include sensitivity table generation option (vary key assumptions)
- Ensure all formulas are auditable and traceable
