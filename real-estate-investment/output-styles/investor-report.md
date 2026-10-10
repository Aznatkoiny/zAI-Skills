---
name: Investor Report
description: Formal investment memo format for real estate deal analyses, portfolio reviews and market research meant for investors or lenders. Executive summary, financial tables, scenarios, risks and a Go / Conditional / Pass recommendation.
keep-coding-instructions: true
---

# Investor Report Output Style

Use this structure when you deliver a full analysis (a deal, a portfolio review, a market study). Answer quick questions and follow-ups conversationally, in a few sentences or a small table, without the memo structure.

## Structure

1. **Executive Summary** (3-5 lines): property type, location, price, size; cap rate, cash-on-cash, DSCR, IRR; the recommendation, **Go / Conditional / Pass**, with any conditions stated as numbers.
2. **Property Overview**: type, address, market, units or square footage, year built, condition.
3. **Financial Analysis**: income, operating expenses and capex reserve, debt terms and payment, and the cash flow summary (NOI, debt service, cash flow), each as a table.
4. **Return Metrics**

   | Metric | Year 1 | Hold-period average | Notes |
   |--------|--------|------------|-------|
   | NOI | | | |
   | Cap Rate | | | |
   | Cash-on-Cash | | | |
   | DSCR | | | |
   | IRR (hold period, 10 years by default) | | | |
   | Equity Multiple | | | |

5. **Scenarios**: bear / base / bull as defined in `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/references/benchmarks.md` §Scenarios, with IRR, CoC and DSCR for each.
6. **Risks**: 4-6 key risks, each with a mitigation.
7. **Tax Considerations** (when relevant): depreciation, cost segregation potential, 1031 eligibility, entity notes.
8. **Recommendation**: Go / Conditional / Pass, the conditions, and the due-diligence items that would change it.
9. **Assumptions**: every major assumption, marked as user-provided, data-backed (with source) or plugin default.

## Formatting

- Financial data in markdown tables; thousands with commas ($1,250,000); percentages to one decimal (6.5%).
- Professional tone, no emojis.
- End with one line: "Educational analysis, not investment, tax or legal advice."
