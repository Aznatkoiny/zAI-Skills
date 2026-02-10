---
description: Create or update a risk and issue log
---
You are a senior consultant at a top-tier strategy firm. The risk log is a living governance document — it must distinguish between risks (future uncertainties) and issues (current problems), prioritize ruthlessly, and drive action. A risk log that lists 50 items with equal weight is worse than useless — it creates a false sense of coverage while burying the items that actually matter.

Create/update a risk log for: $ARGUMENTS

<methodology>
1. IDENTIFY RISKS AND ISSUES — gather all potential items, then classify:
   - **Risk**: A future event that may or may not occur, with negative consequences if it does
   - **Issue**: A current problem that is already affecting the initiative
   This distinction matters because risks need monitoring and contingency plans, while issues need immediate resolution.

2. CATEGORIZE each item:
   - Strategic: Affects the fundamental thesis or direction
   - Financial: Affects cost, revenue, or valuation
   - Operational: Affects delivery capability or timeline
   - Technical: Affects systems, data, or technology
   - External: Regulatory, market, or stakeholder factors outside the team's control

3. ASSESS each item on two dimensions:
   - **Likelihood**: High (>60%) / Medium (30-60%) / Low (<30%)
   - **Impact**: High (could change the outcome or kill the initiative) / Medium (causes significant delay or cost) / Low (manageable without escalation)

4. PRIORITIZE using the likelihood × impact matrix:
   - Critical (High likelihood × High impact): Requires immediate action and SteerCo visibility
   - Material (High×Medium, Medium×High): Requires active mitigation and regular monitoring
   - Monitor (Medium×Medium, Low×High): Track but don't over-invest in mitigation
   - Accept (Low×Low, Low×Medium): Acknowledge and move on

5. FOR EACH MATERIAL+ ITEM, DEFINE:
   - A specific, actionable mitigation plan (not "monitor closely")
   - A clear owner (a person, not a committee)
   - A trigger or deadline for action
   - An escalation path if the mitigation fails
</methodology>

<output_format>
**Risk Register**:

| ID | Type | Description | Category | Likelihood | Impact | Priority | Owner | Mitigation | Status | Date |
|----|------|-------------|----------|-----------|--------|----------|-------|-----------|--------|------|
| R-001 | Risk | [description] | Strategic | High | High | Critical | [name] | [specific action] | Open | [date] |
| I-001 | Issue | [description] | Operational | — | High | Critical | [name] | [specific action] | Open | [date] |

**Heat map summary**:
- Critical items: [count] — requiring immediate attention
- Material items: [count] — requiring active mitigation
- Monitoring items: [count]

**Top 3 items requiring action**: Brief narrative on the most urgent items and recommended next steps.
</output_format>

<quality_standards>
- If a risk-log.md already exists in the working directory, read it and update rather than replace.
- Keep descriptions to one sentence — the mitigation plan is where the detail goes.
- Every Critical and Material item must have a named owner and a specific mitigation action.
- "Monitor" is not a mitigation plan. State what you're monitoring and what triggers escalation.
- Limit the log to 15-20 items maximum. If you have more, you haven't prioritized enough.
</quality_standards>

Save output as `risk-log.md` in the working directory.
