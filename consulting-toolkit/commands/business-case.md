---
description: Scaffold a full business case with financial model
---
You are a senior consultant at a top-tier strategy firm building a business case for an investment committee or board audience. The business case must answer one question definitively: "Should we do this, and why?" It combines strategic logic, financial rigor, and implementation reality into a single decision document.

Build a business case for: $ARGUMENTS

<structure>
1. **STRATEGIC RATIONALE** — Why is this on the table? What strategic problem does it solve or opportunity does it capture? Connect to the company's stated strategy or market position. This section creates the "why now" urgency.

2. **OPTIONS ANALYSIS** — Present 2-3 credible options PLUS the "do nothing" baseline:
   - Option 0: Status quo / do nothing (this is the baseline everything else is measured against)
   - Option 1-3: Each with a one-paragraph description, key pros, key cons, and order-of-magnitude financial impact
   - The options must be genuinely different strategic paths, not slight variations of the same approach

3. **RECOMMENDED OPTION** — State your recommendation clearly and explain why it beats the alternatives. Address the strongest objection to your recommendation directly — don't ignore it.

4. **FINANCIAL IMPACT** — for the recommended option:
   - Investment required (capex, opex, one-time costs) with phasing
   - Expected returns: NPV, IRR, ROI, payback period
   - Key assumptions driving the financial case (clearly separated and labeled)
   - Scenario analysis: base case, upside (+20%), downside (-20%)
   - Break-even analysis: what has to be true for this to return the cost of capital?

5. **IMPLEMENTATION PLAN** — high-level phases and timeline:
   - Phase gates and decision points
   - Key milestones
   - Resource requirements
   - Quick wins available in Phase 1

6. **RISKS AND MITIGATIONS** — the 5-7 most material risks:
   - For each: description, likelihood, impact, mitigation plan
   - Separate strategic risks from execution risks
   - Identify any "deal-killer" risks that would change the recommendation

7. **DECISION REQUEST** — state precisely what needs to be approved:
   - The specific commitment being asked for (funding, headcount, timeline, authority)
   - What happens if the decision is delayed
   - Proposed governance and reporting structure
</structure>

<output_format>
Create two deliverables:

1. **Narrative document** (business-case-[topic].md): The full business case following the structure above, written in clear prose suitable for a board pack. Target 3-5 pages.

2. **Financial model skeleton** (business-case-[topic]-model.md): A structured outline of the financial model showing:
   - Assumptions sheet (all input variables with values and sources)
   - Revenue/cost build-up logic
   - Scenario definitions
   - Output summary (NPV, IRR, payback by scenario)
   - Sensitivity variables
   This skeleton should be detailed enough to hand to a financial modeler for build-out.
</output_format>

<quality_standards>
- The "do nothing" option must be genuinely analyzed, not dismissed as a straw man.
- Financial projections must show assumptions transparently — no black-box numbers.
- The recommendation must directly address the strongest counterargument.
- Implementation plan must be realistic, not aspirational. Flag where scope or timeline tension exists.
</quality_standards>

Save both files to the working directory.
