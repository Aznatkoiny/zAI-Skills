---
description: BRRRR calculator (Buy, Rehab, Rent, Refinance, Repeat) — cash invested, refinance cash-out, capital recycled, post-refi cash flow and a Go / Conditional / Pass verdict
argument-hint: "[quick] [address or deal details]"
---

# BRRRR Strategy Calculator

Request: $ARGUMENTS

Framework and rules of thumb: `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/references/property-types.md` §BRRRR Method Framework. Thresholds: `${CLAUDE_PLUGIN_ROOT}/skills/real-estate-investment/references/benchmarks.md` (BRRRR rows).

## 1. Inputs

**Quick mode** (the request starts with `quick`, or the user gave only the essentials): five inputs, **purchase price, rehab cost, ARV, monthly rent, refinance LTV**. Ask for any of the five that are missing in one question, default everything else, and list the defaults.

**Full mode** (otherwise): use whatever the user gave and fill the gaps with these defaults, listing them:

| Phase | Input | Default |
|---|---|---|
| Buy | Closing costs | 3% of price |
| | Acquisition financing | All cash (hard-money loans: user gives down payment %, rate, points) |
| Rehab | Timeline | 4 months |
| | Holding costs | 0.5% of price per month for taxes, insurance and utilities, plus interest on any acquisition loan |
| Rent | Vacancy | 6% |
| | Operating expenses | 40% of effective rent (benchmarks.md) |
| Refinance | LTV | 75% of ARV |
| | Rate | Latest 30-year rate + investor spread (benchmarks.md) |
| | Term | 30 years |
| | Closing costs | 2.5% of the new loan |

If the request is empty, ask for the five quick inputs with an example: `/brrrr quick $120k buy, $45k rehab, $230k ARV, $1,750 rent, 75% LTV`.

## 2. Calculate

**Cash invested** (what the investor actually puts in):

```
Cash Invested = (Purchase Price − Acquisition Loan)   ← the down payment; the full price if cash
              + Purchase Closing Costs
              + Rehab Cost (unless the acquisition loan funds it)
              + Holding Costs
```

**Refinance**:

```
New Loan        = ARV × Refinance LTV
Cash Out        = New Loan − Acquisition Loan Payoff − Refinance Closing Costs
Cash Left In    = Cash Invested − Cash Out   (zero or less = all capital recycled)
Equity          = ARV − New Loan
```

**Rent after refinance** (monthly):

```
Cash Flow = Rent × (1 − Vacancy) − Operating Expenses − New Loan P&I
CoC       = Annual Cash Flow / Cash Left In   (infinite if Cash Left In ≤ 0 and cash flow is positive)
DSCR      = Annual NOI / Annual New Loan P&I
```

**Rules of thumb**: 70% rule (price + rehab ≤ 70% × ARV); 1% rule (monthly rent ≥ 1% of price + rehab).

## 3. Present

Stage by stage, compactly:

- **Buy**: price, closing costs, cash in
- **Rehab**: budget, timeline, holding costs, cash invested to date
- **Rent**: rent, vacancy, expenses, rule checks (70% and 1%, pass/fail)
- **Refinance**: new loan, cash out, cash left in, equity
- **Repeat**: capital recycled (cash out as % of cash invested), post-refi cash flow, CoC on cash left in, DSCR

Then the **verdict**: Go / Conditional / Pass against benchmarks.md's BRRRR rows, with conditions as numbers ("works if ARV appraises at $220k or more").

Always show what happens if the appraisal comes in 10% below ARV (new loan, cash left in, cash flow), since a low appraisal is the most common way a BRRRR fails, and note the seasoning period many lenders require before a cash-out refinance (often 6-12 months). Flag an ARV that isn't backed by comparable sales. End with one line: educational analysis, not investment advice.
