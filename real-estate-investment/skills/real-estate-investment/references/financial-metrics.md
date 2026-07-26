# Financial Metrics & Pro Forma Modeling

## Table of Contents
- [Quick Reference Table](#quick-reference-table)
- [Core Metrics](#core-metrics)
  - [Net Operating Income (NOI)](#1-net-operating-income-noi)
  - [Capitalization Rate (Cap Rate)](#2-capitalization-rate-cap-rate)
  - [Cash-on-Cash Return](#3-cash-on-cash-return-coc)
  - [Debt Service Coverage Ratio (DSCR)](#4-debt-service-coverage-ratio-dscr)
  - [Internal Rate of Return (IRR)](#5-internal-rate-of-return-irr)
  - [Equity Multiple](#6-equity-multiple)
  - [Gross Rent Multiplier (GRM)](#7-gross-rent-multiplier-grm)
  - [Operating Expense Ratio (OER)](#8-operating-expense-ratio-oer)
  - [Break-even Occupancy Ratio](#9-break-even-occupancy-ratio)
  - [Price per Unit / SF](#10-price-per-unit--sf)
  - [Rent-to-Price Ratio (1% Rule)](#11-rent-to-price-ratio-1-rule)
  - [Debt Yield](#12-debt-yield)
- [Pro Forma Construction](#pro-forma-construction)
- [Python Implementation](#python-implementation)
- [Excel Reference](#excel-reference)

## Quick Reference Table

| Metric | Formula | Typical Range |
|--------|---------|---------------|
| NOI | EGI - OpEx | Property dependent |
| Cap Rate | NOI / Property Value | 4%-10% (market dependent) |
| Cash-on-Cash | (NOI - Debt Service) / Equity | 6%-12% |
| DSCR | NOI / Debt Service | 1.2x minimum (lender requirement) |
| Equity Multiple | Total Distributions / Equity | 1.5x-3.0x (hold period dependent) |
| GRM | Price / Gross Rent | 8-15 (market dependent) |
| OER | OpEx / EGI | Multifamily: 35%-45% |
| Break-even Occupancy | (OpEx + Debt) / PGI | <85% (lender preference) |

---

## Core Metrics

### 1. Net Operating Income (NOI)

**Formula:**
```
NOI = Effective Gross Income - Operating Expenses
```

**What It Measures:** Property operating performance before debt service.

**Python:**
```python
def calculate_noi(effective_gross_income, operating_expenses):
    """Calculate Net Operating Income"""
    return effective_gross_income - operating_expenses

# Example
noi = calculate_noi(500000, 200000)
print(f"NOI: ${noi:,.2f}")  # $300,000.00
```

**Excel:** `=B2-C2` where B2 = EGI, C2 = OpEx

---

### 2. Capitalization Rate (Cap Rate)

**Formula:**
```
Cap Rate = NOI / Property Value
```

**What It Measures:** Unlevered yield on property; quick valuation metric.

**When to Use:** Compare similar properties, estimate value from NOI.

**Python:**
```python
def calculate_cap_rate(noi, property_value):
    """Calculate Cap Rate"""
    return noi / property_value

def estimate_value_from_cap_rate(noi, cap_rate):
    """Reverse: estimate value"""
    return noi / cap_rate

# Example
cap_rate = calculate_cap_rate(300000, 4000000)
print(f"Cap Rate: {cap_rate:.2%}")  # 7.50%

value = estimate_value_from_cap_rate(300000, 0.075)
print(f"Estimated Value: ${value:,.0f}")
```

**Excel:** `=B2/C2` where B2 = NOI, C2 = Property Value

---

### 3. Cash-on-Cash Return (CoC)

**Formula:**
```
CoC = (NOI - Annual Debt Service) / Total Cash Invested
```

**What It Measures:** Annual levered return on equity invested.

**When to Use:** Evaluate first-year or stabilized returns; compare leverage scenarios.

**Python:**
```python
def calculate_cash_on_cash(noi, annual_debt_service, total_cash_invested):
    """Calculate Cash-on-Cash Return"""
    annual_cash_flow = noi - annual_debt_service
    return annual_cash_flow / total_cash_invested

# Example
coc = calculate_cash_on_cash(300000, 180000, 1000000)
print(f"Cash-on-Cash: {coc:.2%}")  # 12.00%
```

**Excel:** `=(B2-C2)/D2` where B2 = NOI, C2 = Debt Service, D2 = Equity

---

### 4. Debt Service Coverage Ratio (DSCR)

**Formula:**
```
DSCR = NOI / Annual Debt Service
```

**What It Measures:** Property's ability to cover debt obligations.

**Typical Requirements:**
- Lenders require DSCR ≥ 1.2x for stabilized properties
- DSCR = 1.0x means break-even (NOI exactly covers debt)

**Python:**
```python
def calculate_dscr(noi, annual_debt_service):
    """Calculate DSCR"""
    return noi / annual_debt_service

# Example
dscr = calculate_dscr(450000, 250000)
print(f"DSCR: {dscr:.2f}x")  # 1.80x

# Check lender requirements
min_dscr = 1.20
if dscr >= min_dscr:
    print(f"✓ Meets minimum DSCR of {min_dscr}x")
else:
    print(f"✗ Below minimum DSCR of {min_dscr}x")
```

**Excel:** `=B2/C2` where B2 = NOI, C2 = Annual Debt Service

---

### 5. Internal Rate of Return (IRR)

**Formula:**
```
0 = CF₀ + CF₁/(1+IRR)¹ + CF₂/(1+IRR)² + ... + CFₙ/(1+IRR)ⁿ
```

**What It Measures:** Annualized return accounting for time value of money.

**Levered vs Unlevered:**
- **Unlevered IRR**: Based on NOI (property performance)
- **Levered IRR**: Based on cash flow after debt service (equity returns)

**Python:**
```python
import numpy_financial as npf

def calculate_irr(cash_flows):
    """Calculate IRR from cash flow array"""
    return npf.irr(cash_flows)

# Example: 5-year hold
cash_flows = [-1000000, 120000, 120000, 120000, 120000, 1320000]
irr = calculate_irr(cash_flows)
print(f"IRR: {irr:.2%}")  # 15.24%

# XIRR for irregular dates
from scipy.optimize import newton
from datetime import datetime

def calculate_xirr(cash_flows, dates, guess=0.1):
    """Calculate XIRR for irregular cash flows"""
    def xnpv(rate, cash_flows, dates):
        min_date = min(dates)
        days = [(d - min_date).days for d in dates]
        return sum([cf / (1 + rate) ** (day / 365.0) for cf, day in zip(cash_flows, days)])

    return newton(lambda r: xnpv(r, cash_flows, dates), guess)

# Example
cfs = [-1000000, 50000, 75000, 100000, 1200000]
dates = [
    datetime(2023, 1, 1),
    datetime(2023, 6, 15),
    datetime(2024, 3, 20),
    datetime(2024, 12, 10),
    datetime(2025, 8, 1)
]
xirr = calculate_xirr(cfs, dates)
print(f"XIRR: {xirr:.2%}")
```

**Excel:**
```excel
=IRR(B2:B12)                    # Regular periods
=XIRR(B2:B12, A2:A12)           # Irregular dates
```

---

### 6. Equity Multiple

**Formula:**
```
Equity Multiple = Total Cash Distributions / Initial Equity Investment
```

**What It Measures:** Gross multiple of money returned (ignores timing).

**Interpretation:**
- 2.5x = investor receives $2.50 for every $1.00 invested
- Should be paired with IRR (2.0x over 3 years ≠ 2.0x over 10 years)

**Python:**
```python
def calculate_equity_multiple(total_distributions, initial_equity):
    """Calculate Equity Multiple"""
    return total_distributions / initial_equity

def calculate_equity_multiple_from_cf(cash_flows):
    """Calculate from cash flow array (cf[0] = initial investment)"""
    initial_investment = abs(cash_flows[0])
    total_distributions = sum(cash_flows[1:])
    return total_distributions / initial_investment

# Example
em = calculate_equity_multiple_from_cf([-1000000, 120000, 120000, 120000, 120000, 1320000])
print(f"Equity Multiple: {em:.2f}x")  # 1.80x
```

**Excel:** `=SUM(B3:B12)/ABS(B2)` where B2 = initial investment, B3:B12 = distributions

---

### 7. Gross Rent Multiplier (GRM)

**Formula:**
```
GRM = Property Price / Gross Annual Rent
```

**What It Measures:** Quick screening metric for relative pricing.

**Interpretation:** Lower GRM = higher expected yield.

**Python:**
```python
def calculate_grm(property_price, gross_annual_rent):
    """Calculate GRM"""
    return property_price / gross_annual_rent

def estimate_value_from_grm(gross_annual_rent, market_grm):
    """Estimate value using market GRM"""
    return gross_annual_rent * market_grm

# Example
grm = calculate_grm(1200000, 100000)
print(f"GRM: {grm:.2f}")  # 12.00

# Compare properties
import pandas as pd
properties = pd.DataFrame({
    'Property': ['A', 'B', 'C'],
    'Price': [1200000, 850000, 2000000],
    'Rent': [100000, 85000, 150000]
})
properties['GRM'] = properties['Price'] / properties['Rent']
print(properties)
```

**Excel:** `=B2/C2` where B2 = Price, C2 = Gross Annual Rent

---

### 8. Operating Expense Ratio (OER)

**Formula:**
```
OER = Operating Expenses / Effective Gross Income
```

**Typical Ranges:**
- **Multifamily**: 35%-45% (good range: 35%-40%)
- **Office**: 35%-55%
- **Retail**: 20%-30% or 60%-80% (lease structure dependent)
- **Industrial**: 15%-25%

**Python:**
```python
def calculate_oer(operating_expenses, effective_gross_income):
    """Calculate OER"""
    return operating_expenses / effective_gross_income

def benchmark_oer(oer, property_type):
    """Benchmark against typical ranges"""
    benchmarks = {
        'multifamily': (0.35, 0.45),
        'office': (0.35, 0.55),
        'retail': (0.20, 0.30),
        'industrial': (0.15, 0.25)
    }

    if property_type.lower() in benchmarks:
        low, high = benchmarks[property_type.lower()]
        if low <= oer <= high:
            return f"Within range ({low:.0%}-{high:.0%})"
        elif oer < low:
            return f"Below range - Very efficient"
        else:
            return f"Above range - Review expenses"
    return "Unknown property type"

# Example
oer = calculate_oer(200000, 500000)
print(f"OER: {oer:.1%}")  # 40.0%
print(benchmark_oer(oer, 'multifamily'))
```

**Excel:** `=B2/C2` where B2 = OpEx, C2 = EGI

---

### 9. Break-even Occupancy Ratio

**Formula:**
```
Break-even Occupancy = (Operating Expenses + Debt Service) / Potential Gross Income
```

**What It Measures:** Minimum occupancy to cover OpEx + debt.

**Lender Preference:** ≤85% for reasonable cushion.

**Python:**
```python
def calculate_breakeven_occupancy(operating_expenses, debt_service, potential_gross_income):
    """Calculate Break-even Occupancy"""
    return (operating_expenses + debt_service) / potential_gross_income

# Example
beo = calculate_breakeven_occupancy(200000, 180000, 500000)
print(f"Break-even Occupancy: {beo:.1%}")  # 76.0%

# Calculate margin of safety
current_occupancy = 0.92
margin = current_occupancy - beo
print(f"Margin of Safety: {margin:.1%}")  # 16.0%

# Check lender requirements
if beo <= 0.85:
    print("✓ Acceptable break-even (<85%)")
else:
    print(f"✗ Exceeds 85% threshold by {(beo - 0.85):.1%}")
```

**Excel:** `=(B2+C2)/D2` where B2 = OpEx, C2 = Debt Service, D2 = PGI

---

### 10. Price per Unit / SF

**Formulas:**
```
Price per Unit = Total Price / Number of Units
Price per SF = Total Price / Total Square Footage
```

**When to Use:** Compare properties of different sizes; market benchmarking.

**Python:**
```python
def calculate_price_per_unit(total_price, num_units):
    """Calculate Price per Unit"""
    return total_price / num_units

def calculate_price_per_sf(total_price, total_sf):
    """Calculate Price per SF"""
    return total_price / total_sf

# Example
ppu = calculate_price_per_unit(5000000, 50)
ppsf = calculate_price_per_sf(5000000, 45000)

print(f"Price per Unit: ${ppu:,.0f}")  # $100,000
print(f"Price per SF: ${ppsf:,.2f}")   # $111.11

# Compare multiple properties
import pandas as pd
df = pd.DataFrame({
    'Property': ['A', 'B', 'C'],
    'Price': [5000000, 7500000, 3200000],
    'Units': [50, 75, 32],
    'SF': [45000, 68000, 30000]
})
df['Price/Unit'] = df['Price'] / df['Units']
df['Price/SF'] = df['Price'] / df['SF']
print(df)
```

**Excel:**
```excel
Price/Unit: =B2/C2
Price/SF: =B2/D2
```

---

### 11. Rent-to-Price Ratio (1% Rule)

**Formula:**
```
Rent-to-Price Ratio = Gross Monthly Rent / Purchase Price
```

**What It Measures:** Fast screening ratio for rental yield; the inverse view of GRM.

**Interpretation:**
- **1% rule**: monthly rent ≥ 1% of price suggests strong cash flow potential
- 0.7%-1.0% is common in appreciating metros; treat the rule as a screen, not a verdict
- Always follow up with a full pro forma — the rule ignores taxes, OpEx, and financing

**Python:**
```python
def calculate_rent_to_price(monthly_rent, purchase_price):
    """Calculate Rent-to-Price Ratio"""
    return monthly_rent / purchase_price

def passes_one_percent_rule(monthly_rent, purchase_price):
    """Screen against the 1% rule"""
    return calculate_rent_to_price(monthly_rent, purchase_price) >= 0.01

# Example
ratio = calculate_rent_to_price(2200, 250000)
print(f"Rent-to-Price: {ratio:.2%}")  # 0.88%
print("Passes 1% rule" if passes_one_percent_rule(2200, 250000) else "Fails 1% rule")
```

**Excel:** `=B2/C2` where B2 = Monthly Rent, C2 = Purchase Price (format as %)

---

### 12. Debt Yield

**Formula:**
```
Debt Yield = NOI / Loan Amount
```

**What It Measures:** Lender's unlevered return if forced to foreclose; a leverage cap independent of interest rates and amortization.

**Typical Requirements:**
- CMBS and institutional lenders: ≥ 8%-10% minimum
- Unlike DSCR, debt yield cannot be engineered with longer amortization or lower rates

**Python:**
```python
def calculate_debt_yield(noi, loan_amount):
    """Calculate Debt Yield"""
    return noi / loan_amount

def max_loan_from_debt_yield(noi, min_debt_yield=0.10):
    """Reverse: maximum loan a lender will size at a given debt yield floor"""
    return noi / min_debt_yield

# Example
dy = calculate_debt_yield(300000, 3200000)
print(f"Debt Yield: {dy:.2%}")  # 9.38%

max_loan = max_loan_from_debt_yield(300000, 0.10)
print(f"Max Loan @ 10% debt yield: ${max_loan:,.0f}")  # $3,000,000
```

**Excel:** `=B2/C2` where B2 = NOI, C2 = Loan Amount

---

## Pro Forma Construction

### Standard Waterfall Structure

```
1. Gross Potential Rent (GPR)
   + Other Income (2%-5% of rent: parking, laundry, fees)
   ─────────────────────────
2. = Potential Gross Income (PGI)

3. - Vacancy & Credit Loss (5%-15% depending on property class/type)
   ─────────────────────────
4. = Effective Gross Income (EGI)

5. - Operating Expenses
     • Property Taxes
     • Insurance (0.5%-1.5% of value)
     • Utilities
     • Repairs & Maintenance (5%-15% of EGI)
     • Property Management (3%-5% of EGI)
     • Administrative
     • Payroll
     • Contract Services
   ─────────────────────────
6. = Net Operating Income (NOI)

7. - Debt Service (Principal + Interest)
   ─────────────────────────
8. = Cash Flow Before CapEx

9. - CapEx Reserves (5%-10% of EGI or $250-$500/unit)
   ─────────────────────────
10. = Net Cash Flow
```

### Growth Assumptions

**Rent Growth:**
- Conservative: 2%-3% annually
- Long-run average: ~3%
- Stabilization: 1.5% Y1, 2.5% Y2, 3% Y3+
- Must be supported by market data

**Expense Growth:**
- Typical: 2%-3% annually
- Property taxes: 2.5%-3%
- Utilities: 3%-4% (inflation sensitive)
- Insurance: 3%-5% (volatile)

### CapEx Reserves

**Major Categories:** Roof, HVAC, parking, plumbing, electrical, elevators, unit renovations

**Common Methods:**
- Percentage: 5%-10% of EGI
- Per unit: $250-$500 annually (multifamily)
- Per SF: $0.25-$0.75 (commercial)
- Component-based: Calculate replacement cycles

**Note:** Not included in NOI, but deducted from cash flow.

### Best Practices

1. Use conservative assumptions (underestimate income, overestimate expenses)
2. Separate market rent from in-place rent
3. Model stabilization period explicitly
4. Include sensitivity analysis on key drivers
5. Support all assumptions with market data
6. Calculate multiple return metrics (IRR, EM, CoC, NPV)
7. Model actual loan terms and amortization
8. Include exit assumptions (cap rate, selling costs)

---

## Python Implementation

### Canonical Script: `scripts/pro_forma.py`

The complete `RealEstateProForma` model lives as a runnable module at
`scripts/pro_forma.py` (relative to this skill's directory). Run it — do not
re-write the model from prose. It builds the full year-by-year projection
(GPR → vacancy → EGI → OpEx → NOI → debt service → net cash flow), models the
exit sale, and reports IRR, equity multiple, NPV @ 8/10/12%, purchase cap
rate, year-1 cash-on-cash, and year-1 DSCR.

```bash
pip install numpy numpy-financial   # one-time

python scripts/pro_forma.py --sample-input > inputs.json    # JSON input template
python scripts/pro_forma.py --input inputs.json --table     # human-readable summary
python scripts/pro_forma.py --input inputs.json --output results.json   # full JSON
```

Input schema (three top-level keys, see `--sample-input` for a filled example):

| Key | Fields |
|-----|--------|
| `property` | `purchase_price`, `units` + `annual_rent_per_unit` (or `annual_gross_rent`), `other_income_pct`, `vacancy_rate`, `opex_ratio` |
| `loan` | `ltv`, `interest_rate` (annual), `amortization_years` |
| `assumptions` | `holding_period`, `rent_growth`, `expense_growth`, `capex_pct`, `exit_cap_rate`, `selling_costs_pct` |

Model mechanics worth knowing (all implemented in the script):

- **Expense handling (corrected):** the Year-1 OpEx base equals Year-1 EGI × `opex_ratio`; from Year 2 on it escalates at `expense_growth` only — OpEx is never re-derived from grown revenue, so rent growth and expense growth stay independent.
- **Loan balance:** `npf.pmt` returns a negative outflow; it is passed to `npf.fv` as-is and the result negated: `balance = -npf.fv(rate, year, payment, loan_amount)`.
- **Exit:** sale value = final-year NOI / `exit_cap_rate`, less selling costs and the remaining loan balance; the final year's total cash flow adds net sale proceeds.
- **Cash flow vector:** index 0 is `-equity` at acquisition, 1..N are annual equity cash flows; IRR, NPV, and equity multiple all run off this dated vector.

For a purchase-price × interest-rate stress grid on the same input file, run
`scripts/sensitivity.py` (documented in `references/advanced-analysis.md`
§Sensitivity).

### Key numpy-financial Functions

```python
import numpy_financial as npf

# 1. PMT - Loan payment
payment = npf.pmt(rate, nper, pv, fv=0, when='end')
# Example
monthly_payment = npf.pmt(0.05/12, 30*12, 200000)
print(f"Monthly Payment: ${-monthly_payment:,.2f}")

# 2. IPMT - Interest portion
interest = npf.ipmt(rate, per, nper, pv)
month_1_interest = npf.ipmt(0.05/12, 1, 30*12, 200000)

# 3. PPMT - Principal portion
principal = npf.ppmt(rate, per, nper, pv)
month_1_principal = npf.ppmt(0.05/12, 1, 30*12, 200000)

# 4. IRR - Internal rate of return
cash_flows = [-1000000, 120000, 120000, 120000, 120000, 1320000]
irr = npf.irr(cash_flows)
print(f"IRR: {irr:.2%}")

# 5. NPV - Net present value
npv = npf.npv(0.10, cash_flows)
print(f"NPV @ 10%: ${npv:,.0f}")

# 6. FV - Future value (remaining loan balance)
# monthly_payment from npf.pmt is already negative (an outflow) — pass as-is
remaining_balance = -npf.fv(0.05/12, 60, monthly_payment, 200000)
print(f"Balance after 5 years: ${remaining_balance:,.0f}")

# 7. PV - Present value (loan amount from payment)
loan_amount = -npf.pv(0.05/12, 30*12, 1073.64)
print(f"Loan Amount: ${loan_amount:,.0f}")
```

---

## Excel Reference

### Core Financial Functions

| Python | Excel | Example | Notes |
|--------|-------|---------|-------|
| `npf.pmt()` | `=PMT(rate, nper, pv, [fv], [type])` | `=PMT(5%/12, 360, 200000)` | Returns negative |
| `npf.ipmt()` | `=IPMT(rate, per, nper, pv)` | `=IPMT(5%/12, 1, 360, 200000)` | Interest portion |
| `npf.ppmt()` | `=PPMT(rate, per, nper, pv)` | `=PPMT(5%/12, 1, 360, 200000)` | Principal portion |
| `npf.fv()` | `=FV(rate, nper, pmt, [pv])` | `=FV(5%/12, 60, -1073.64, 200000)` | Remaining balance |
| `npf.pv()` | `=PV(rate, nper, pmt, [fv])` | `=PV(5%/12, 360, -1073.64)` | Loan amount |
| `npf.irr()` | `=IRR(values, [guess])` | `=IRR(B2:B12)` | Array starts with CF₀ |
| `npf.npv()` | `=NPV(rate, values)` | `=NPV(10%, B3:B12) + B2` | **Add B2 separately!** |
| XIRR (scipy) | `=XIRR(values, dates)` | `=XIRR(B2:B12, A2:A12)` | Irregular dates |
| XNPV (scipy) | `=XNPV(rate, values, dates)` | `=XNPV(10%, B2:B12, A2:A12)` | Irregular NPV |

### Real Estate Metrics

| Metric | Excel Formula |
|--------|---------------|
| NOI | `=B2-C2` (EGI - OpEx) |
| Cap Rate | `=B2/C2` (NOI / Value) |
| Cash-on-Cash | `=(B2-C2)/D2` ((NOI - Debt) / Equity) |
| DSCR | `=B2/C2` (NOI / Debt Service) |
| Equity Multiple | `=SUM(B3:B12)/ABS(B2)` |
| GRM | `=B2/C2` (Price / Rent) |
| OER | `=B2/C2` (OpEx / EGI) |
| Break-even Occupancy | `=(B2+C2)/D2` ((OpEx + Debt) / PGI) |
| Price/Unit | `=B2/C2` (Price / Units) |
| Rent-to-Price | `=B2/C2` (Monthly Rent / Price) |
| Debt Yield | `=B2/C2` (NOI / Loan Amount) |

### Important Excel NPV Note

Excel's NPV assumes first value is end of period 1, not period 0:

```excel
Incorrect: =NPV(10%, B2:B12)
Correct:   =NPV(10%, B3:B12) + B2
```

### Amortization Schedule Template

Sign convention: every column is a **positive** number. Excel's `PMT` returns a
negative value, so negate it in column C — then `Principal = Payment - Interest`
is sign-consistent.

```excel
A: Period (1 to 360)
B: Beginning Balance
   B2: =Loan_Amount
   B3: =F2 (previous ending balance)
C: Payment (negated so it is positive)
   C2: =-PMT($Rate/12, $Term*12, $Loan_Amount)
D: Interest
   D2: =B2*$Rate/12
E: Principal
   E2: =C2-D2
F: Ending Balance
   F2: =B2-E2
```

### Growth Escalations

```excel
# Compound growth
Year 1: =Base_Value
Year 2: =Base_Value * (1 + Growth_Rate)^1
Year N: =Base_Value * (1 + Growth_Rate)^(N-1)

# Using absolute/relative references
Year 1: =$B$2
Year 2: =$B$2 * (1 + $C$2)^(A3-A2)
```
