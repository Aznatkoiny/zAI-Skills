---
name: Quick Screen
description: Ultra-concise deal screening format with compact metrics table, pass/fail indicators, and one-line verdict. Use when rapidly evaluating multiple properties or doing initial deal screening.
keep-coding-instructions: true
---

# Quick Screen Output Style

When generating output in this style, format for rapid deal evaluation:

## Structure Requirements

Maximum 20-30 lines of output total.

1. **Verdict Line** (first line)
   - Format: `PASS`, `FAIL`, or `REVIEW` followed by brief 5-8 word reason
   - Example: `PASS - Strong CoC return with healthy DSCR`
   - Example: `FAIL - Below market rents, negative cash flow`
   - Example: `REVIEW - Needs renovation analysis`

2. **Compact Metrics Table** (single table format)
   ```
   | Metric      | Value     | Target    | Status |
   |-------------|-----------|-----------|--------|
   | Price       | $xxx,xxx  | Market    | ✓ or ✗ |
   | Gross Rent  | $x,xxx/mo | Market    | ✓ or ✗ |
   | Cap Rate    | x.x%      | >6%       | ✓ or ✗ |
   | CoC Return  | x.x%      | >8%       | ✓ or ✗ |
   | DSCR        | x.xx      | >1.25     | ✓ or ✗ |
   | 1% Rule     | x.x%      | >1%       | ✓ or ✗ |
   ```
   - Use ✓ for meets target, ✗ for fails target
   - Adjust targets based on property type and market

3. **Key Risk** (one line)
   - Format: `Risk: [brief description]`

4. **Key Opportunity** (one line)
   - Format: `Opportunity: [brief description]`

## Formatting Rules

- No narrative explanations
- No section headers beyond table
- No assumptions, disclaimers, or supplementary text
- Numbers: Use commas (e.g., $1,250,000)
- Percentages: One decimal place (e.g., 6.5%)
- Designed for scanning 5-10 properties rapidly
