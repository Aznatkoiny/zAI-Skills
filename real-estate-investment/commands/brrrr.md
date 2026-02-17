---
description: BRRRR strategy calculator — Buy, Rehab, Rent, Refinance, Repeat analysis
---

# BRRRR Strategy Calculator

ARGUMENTS: Optional property address or "quick" for streamlined input

## Instructions

When this command is invoked, analyze a BRRRR investment opportunity:

### 1. Load Reference Material

Read the property types reference for residential guidance:
the `references/property-types.md` file from the `real-estate-investment` skill in this plugin

### 2. Collect BRRRR Inputs

Use AskUserQuestion to gather:

**Purchase Phase:**
- Purchase price
- Purchase closing costs (default: 2-3% of price)
- Initial loan terms (if financing): down payment %, interest rate, term

**Rehab Phase:**
- Estimated rehab cost (itemized or total)
- Rehab timeline (months)
- Holding costs during rehab: loan payments, utilities, taxes, insurance

**ARV (After Repair Value):**
- After-repair value estimate (from comps)
- Source of ARV (appraisal, Zillow, agent CMA)

**Rent Phase:**
- Expected monthly rent after rehab
- Vacancy rate assumption (default: 8%)
- Operating expenses (% of gross rent or itemized)

**Refinance Phase:**
- Refinance loan-to-value (LTV) ratio (typical: 75-80% of ARV)
- Refinance interest rate and term
- Refinance closing costs (default: 2-3% of new loan)

### 3. Calculate Total Investment

Compute all-in cash investment:
```
Total Investment = Purchase Price
                   + Purchase Closing Costs
                   + Down Payment (if financed)
                   + Rehab Cost
                   + Holding Costs
                   - Initial Loan Amount (if applicable)
```

### 4. Validate with Rules of Thumb

Check against BRRRR rules and flag pass/fail:

**70% Rule:**
- Formula: `Purchase Price + Rehab ≤ 70% × ARV`
- Pass/Fail indicator
- Margin of safety

**1% Rule:**
- Formula: `Monthly Rent ≥ 1% × Total Investment`
- Pass/Fail indicator
- Actual percentage achieved

**2% Rule (Aggressive):**
- Formula: `Monthly Rent ≥ 2% × Purchase Price`
- Pass/Fail indicator

### 5. Analyze Cash Flow After Refinance

Calculate post-refinance operating performance:
- New loan amount: `ARV × Refinance LTV`
- Monthly debt service on new loan
- Monthly cash flow: `(Monthly Rent × (1 - Vacancy Rate)) - Operating Expenses - Debt Service`
- Annual cash-on-cash return on remaining equity

### 6. Calculate Refinance Outcome

Determine capital recycling:
```
Cash Out at Refinance = New Loan Amount
                        - Remaining Balance on Initial Loan
                        - Refinance Closing Costs

Equity Left in Deal = ARV - New Loan Amount

Capital Recycled = Cash Out at Refinance
Remaining Investment = Total Investment - Capital Recycled
```

**Infinite Return Check:**
- If `Capital Recycled ≥ Total Investment`, investor achieves infinite return (100% capital recovery)

### 7. Present Stage-by-Stage Breakdown

Format output as clear sections:

**Stage 1 - BUY:**
- Purchase price and costs
- All-in acquisition cost

**Stage 2 - REHAB:**
- Rehab budget and timeline
- Holding costs during construction
- Total investment to date

**Stage 3 - RENT:**
- Expected rent vs 1% and 2% rules
- Monthly cash flow before refinance
- Rule validation (pass/fail table)

**Stage 4 - REFINANCE:**
- New loan amount and terms
- Cash-out proceeds
- Equity remaining in property
- Closing costs

**Stage 5 - REPEAT:**
- Total capital recycled for next deal
- Remaining cash invested in this property
- Cash-on-cash return on remaining equity
- Assessment of deal quality

### 8. Provide Go/No-Go Recommendation

Recommend whether to proceed based on:
- All rules of thumb passing
- Positive post-refinance cash flow
- Acceptable cash-on-cash return (target: >15%)
- Sufficient equity cushion (>20% remaining)

## Notes

- Flag if ARV assumption seems aggressive (verify with multiple comps)
- Warn about refinance risk: What if property doesn't appraise at ARV?
- Consider exit strategy if refinance doesn't work out
- Highlight infinite return achievement if applicable
