---
name: Investor Report
description: Formal investment analysis report format with executive summary, financial tables, risk assessment, and professional presentation. Use when generating deal analysis, portfolio reviews, or market research for investor consumption.
keep-coding-instructions: true
---

# Investor Report Output Style

When generating output in this style, format as a formal investment memorandum:

## Structure Requirements

1. **Executive Summary** (3-5 lines)
   - Key property metrics (type, location, price, size)
   - Primary return metrics (Cap Rate, CoC Return, DSCR)
   - Clear recommendation (Strong Buy / Buy / Hold / Pass)

2. **Property Overview**
   - Property type, address, market
   - Size (units, square footage)
   - Year built, condition, recent improvements

3. **Financial Analysis**
   - Income schedule (rent roll, other income) in table format
   - Expense schedule (operating expenses, CapEx reserve) in table format
   - Debt service (loan terms, payment) in table format
   - Cash flow summary table (NOI, debt service, cash flow)

4. **Return Metrics Table**
   | Metric | Year 1 | 5-Year Avg | Notes |
   |--------|--------|------------|-------|
   | NOI | | | |
   | Cap Rate | | | |
   | Cash-on-Cash | | | |
   | DSCR | | | |
   | IRR (5-yr) | | | |
   | Equity Multiple | | | |

5. **Sensitivity Analysis Table**
   | Scenario | Assumption | CoC Return | Cap Rate |
   |----------|-----------|-----------|----------|
   | Bear | -10% rent, +15% expenses | | |
   | Base | As projected | | |
   | Bull | +10% rent, -10% expenses | | |

6. **Risk Assessment**
   - Bullet list of 4-6 key risks
   - Each with brief mitigation strategy

7. **Tax Considerations**
   - Depreciation schedule overview
   - Cost segregation potential
   - 1031 exchange eligibility (if applicable)
   - Entity structure considerations

8. **Recommendation**
   - Clear go/no-go decision
   - Key conditions or contingencies

9. **Assumptions Section**
   - List all major assumptions used in analysis

## Formatting Rules

- All financial data must be in markdown tables
- Numbers: Use commas for thousands (e.g., $1,250,000)
- Percentages: One decimal place (e.g., 6.5%)
- Professional tone throughout - no casual language, no emojis
- Include disclaimer at end: "This analysis is for educational purposes only and does not constitute investment, tax, or legal advice."
