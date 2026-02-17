---
description: Syndication waterfall distribution calculator — model GP/LP profit splits across IRR hurdles
---

# Syndication Waterfall Calculator

ARGUMENTS: Optional waterfall type ("american" or "european")

## Instructions

When this command is invoked, model a real estate syndication waterfall distribution:

### 1. Load Reference Material

Read the advanced analysis reference for waterfall structures:
the `references/advanced-analysis.md` file from the `real-estate-investment` skill in this plugin

### 2. Collect Syndication Structure

Use AskUserQuestion to gather:

**Equity Structure:**
- Total equity raised (from Limited Partners)
- GP equity contribution (dollar amount or %)
- LP equity contribution (typically 90-95% of total)

**Preferred Return (Pref):**
- Preferred return rate (annual %, typical: 6-8%)
- Is pref cumulative or non-cumulative?
- Is pref compounding?

**Waterfall Tiers:**
- **Tier 1**: Return of capital + Pref (split: typically 100% to LPs until pref met)
- **Tier 2**: GP promote at first hurdle (e.g., 70/30 LP/GP split until 12% IRR)
- **Tier 3**: GP promote at second hurdle (e.g., 60/40 LP/GP split until 15% IRR)
- **Tier 4**: Final split above highest hurdle (e.g., 50/50 LP/GP split above 15% IRR)

**Waterfall Type (skip if provided via ARGUMENTS):**
- **American Waterfall**: Distributions split deal-by-deal as they occur
- **European Waterfall**: All cash flows aggregated, waterfall applies to total returns at exit

### 3. Collect Cash Flow Projections

Ask for investment cash flows:
- Initial equity investment (Year 0, negative)
- Annual operating distributions (Years 1-N)
- Exit/sale proceeds (Year N)

OR allow user to input:
- Hold period
- Assumed total return multiple (e.g., 2.0x equity)
- Distribution pattern (all at exit, or X% annually + exit)

### 4. Calculate Distributions by Tier

For each cash distribution event (American) or total return (European):

**Tier 1 - Return of Capital + Pref:**
```
LP receives 100% until:
- LP capital returned
- Preferred return paid (cumulative total)
```

**Tier 2 - First Hurdle:**
```
Remaining cash split per tier 2 ratio until LP IRR reaches first hurdle
```

**Tier 3 - Second Hurdle (if applicable):**
```
Remaining cash split per tier 3 ratio until LP IRR reaches second hurdle
```

**Tier 4 - Above All Hurdles:**
```
All remaining cash split per final tier ratio
```

### 5. Calculate Returns

Compute for both GP and LP:
- **Total Cash Distributed**
- **Total Return Multiple**: Cash Out ÷ Cash In
- **IRR**: Internal rate of return using actual cash flow timing
- **Profit**: Total Cash - Initial Investment

Additionally for GP:
- GP equity return
- GP promote (carried interest)
- Management fees (if applicable, typical: 1-2% of equity per year)

### 6. Present Waterfall Breakdown

Format output showing:

**Distribution Waterfall Table:**
| Tier | Description | LP Split | GP Split | LP Cumulative | GP Cumulative | LP IRR at Tier End |
|------|-------------|----------|----------|---------------|---------------|--------------------|

**Cash Flow Summary:**
- Year-by-year distributions (for American waterfall)
- Total distributions by tier

**Return Summary:**
| Metric | LP | GP |
|--------|----|----|
| Equity Invested | | |
| Cash Distributed | | |
| Return Multiple | | |
| IRR | | |
| Profit | | |

**GP Economics Breakdown:**
- GP equity return (from GP investment)
- GP promote/carry (from waterfall splits)
- Management fees (if applicable)
- Total GP compensation

### 7. Sensitivity Analysis

Show how distributions change under different return scenarios:
- **Downside**: 1.5x return, 8% IRR
- **Base Case**: User inputs
- **Upside**: 2.5x return, 18% IRR

For each scenario, show LP IRR and GP total compensation.

### 8. Offer Code Generation

Ask if user wants a Python waterfall calculator script that:
- Accepts equity structure and hurdles as parameters
- Calculates distributions from cash flow input
- Outputs detailed waterfall breakdown

If requested, generate and save to working directory.

## Notes

- Explain the difference between American and European waterfalls clearly
- Highlight GP alignment: does GP also invest equity, or only receive promote?
- Flag if promote structure seems aggressive (GP >30% at early hurdles)
- Note tax implications: GP promote typically taxed as long-term capital gains
