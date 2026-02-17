---
description: Short-term rental revenue projection — estimate Airbnb/VRBO income with seasonal modeling
---

# Short-Term Rental Revenue Projection

ARGUMENTS: Optional property address or market name

## Instructions

When this command is invoked, project short-term rental revenue and compare to long-term rental:

### 1. Load Reference Material

Read the property types reference for STR guidance:
the `references/property-types.md` file from the `real-estate-investment` skill in this plugin

### 2. Collect Property Details

Use AskUserQuestion to gather (skip if provided via ARGUMENTS):

**Property Characteristics:**
- Location (city, neighborhood)
- Property type (entire home, condo, unique property)
- Bedrooms and bathrooms
- Square footage
- Notable amenities (pool, hot tub, waterfront, etc.)

**Comparable Data:**
- Average nightly rate (from Airbnb/VRBO comps or AirDNA)
- Check for MCP tools: AirDNA server for market data
- If no MCP available, guide user to research comps manually

### 3. Model Seasonal Revenue

Create month-by-month revenue projection:

**Define Seasons:**
- Peak season months (highest demand)
- Shoulder season months (moderate demand)
- Off-peak season months (lowest demand)

**Seasonal Variations:**
- ADR (Average Daily Rate) by season:
  - Peak: Base ADR × 1.2-1.4
  - Shoulder: Base ADR × 1.0
  - Off-peak: Base ADR × 0.7-0.85

- Occupancy rate by season:
  - Peak: 75-85%
  - Shoulder: 60-70%
  - Off-peak: 40-55%

**Monthly Revenue Calculation:**
```
Monthly Revenue = ADR × Occupancy Rate × Days in Month
```

**Annual Gross Revenue:**
```
Sum of all monthly revenues
```

### 4. Calculate Platform Fees and Expenses

**Platform Fees:**
- Airbnb host fee: ~3% (or 15.5% for simplified pricing)
- VRBO annual subscription or per-booking fee: ~5-8%
- Average total platform fees: 5-10% of gross revenue

**STR-Specific Operating Expenses:**
- **Cleaning**: Per-turnover cost × estimated turnovers (occupancy × 30 / avg stay)
- **Supplies**: Toiletries, coffee, consumables (~2-3% of revenue)
- **Utilities**: Electric, water, gas, internet (~8-12% of revenue, higher than LTR)
- **Property management**: 20-25% of revenue (if using STR management company)
- **Maintenance**: 5-8% of revenue (higher wear and tear than LTR)
- **Insurance**: STR-specific policy (typically 50-100% higher than LTR landlord policy)
- **HOA/Licensing**: HOA fees, STR license, business license
- **Furnishing amortization**: Initial furnishing cost amortized over 3-5 years
- **Marketing**: Photography, listing optimization (~$500-1,000 annually)

**Total STR Expenses:**
Typically 50-60% of gross revenue (compared to 30-40% for LTR)

**Net Operating Income (NOI):**
```
NOI = Gross Revenue - Platform Fees - Operating Expenses
```

### 5. Compare STR vs LTR

**Long-Term Rental Baseline:**
- Research comparable LTR monthly rent for the property
- LTR annual gross income: Monthly Rent × 12
- LTR operating expenses: ~30-40% of gross income
- LTR NOI: Gross Income × (1 - Expense Ratio)

**Break-Even Occupancy Analysis:**
```
Break-Even Occupancy = (LTR Annual NOI + STR Fixed Costs) / (Average ADR × 365 - Variable Cost per Night)
```

This shows the minimum occupancy needed for STR to outperform LTR.

**Comparison Table:**
| Metric | STR | LTR | Difference |
|--------|-----|-----|------------|
| Annual Gross Income | | | |
| Operating Expenses | | | |
| Net Operating Income | | | |
| Management Intensity | High | Low | |
| Regulatory Risk | High | Low | |

### 6. Present Monthly Revenue Projection

Generate detailed month-by-month table:

| Month | ADR | Occupancy | Days | Gross Revenue | Platform Fees | Net Revenue |
|-------|-----|-----------|------|---------------|---------------|-------------|
| Jan | | | 31 | | | |
| Feb | | | 28 | | | |
| ... | | | | | | |
| Dec | | | 31 | | | |
| **Total** | | | **365** | | | |

### 7. Calculate Annual Summary

**Annual Performance:**
- Total gross revenue
- Total platform fees
- Total operating expenses (with breakdown)
- Net operating income
- Average occupancy rate (annual)
- Revenue per available night (RevPAN)

**STR vs LTR Net Income:**
- STR advantage: $X more per year (+Y%)
- Break-even occupancy: Z%
- Current projected occupancy: Z%

### 8. Risk Factors and Recommendations

Highlight key considerations:
- **Regulatory risk**: Check local STR regulations, zoning, HOA rules
- **Seasonality**: Cash flow variance month-to-month
- **Management burden**: Time commitment or management cost
- **Competition**: Saturation in market (# of STR listings per capita)
- **Financing**: Many lenders restrict STR properties or charge higher rates

**Recommendation:**
- Proceed with STR if: occupancy projections are conservative, regulation is stable, investor can handle management
- Consider LTR if: slim STR margin, regulatory uncertainty, passive income preference

### 9. Offer Enhanced Analysis

Ask if user wants:
- Python script for dynamic STR revenue modeling with custom inputs
- Detailed sensitivity analysis (vary ADR and occupancy)
- Market comparison against other STR-friendly markets

## Notes

- Verify local STR regulations before finalizing recommendation
- Consider split strategy: STR in peak season, LTR lease in off-season (if allowed)
- Flag if market shows signs of STR saturation (declining ADR, increasing supply)
- Note that lender STR income projections often use 75% of gross revenue for qualification
