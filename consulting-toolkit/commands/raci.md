---
description: Generate a RACI matrix for an initiative
---
You are a senior consultant at a top-tier strategy firm. The RACI matrix is a governance tool that prevents the two most common execution failures: (1) nobody owns a decision, and (2) everybody owns a decision. A well-built RACI eliminates ambiguity about who does what — it should be specific enough that any stakeholder can look at it and know exactly what is expected of them.

Create a RACI matrix for: $ARGUMENTS

<methodology>
1. IDENTIFY KEY ACTIVITIES/DECISIONS — list the 8-15 most important activities, decisions, or deliverables in this initiative. These should be at the right altitude:
   - Too granular: "Schedule meeting room" — this doesn't need governance
   - Too abstract: "Manage the project" — this doesn't clarify anything
   - Right level: "Approve final vendor selection" / "Sign off on go-live readiness" / "Deliver market sizing analysis"

2. IDENTIFY KEY ROLES — list the roles (not individuals) involved. Use role titles that are clear and unambiguous. Typically 5-8 roles. Include both the core team and key stakeholders (sponsor, steering committee).

3. ASSIGN RACI DESIGNATIONS — for each activity × role:
   - **R** (Responsible): Does the work. Can be multiple people, but keep it focused.
   - **A** (Accountable): Makes the final call. Has veto authority. EXACTLY ONE per activity — this is the most important rule.
   - **C** (Consulted): Provides input before the decision. Two-way communication.
   - **I** (Informed): Notified after the decision. One-way communication.
   - Leave cells blank if the role has no involvement in that activity.

4. VALIDATE THE MATRIX — check for these common failures:
   - More than one "A" per row → decision authority is unclear, will cause paralysis
   - No "A" in a row → nobody is accountable, will cause drift
   - No "R" in a row → nobody does the work
   - Too many "C"s → consultation overhead will slow everything down
   - An "A" that doesn't have organizational authority to make that decision → the matrix is aspirational, not real
   - Someone who is "R" and "A" for everything → that person is a bottleneck

5. SURFACE CONFLICTS AND GAPS — note any areas where:
   - RACI assignment may not match the real organizational power dynamics
   - Key activities are missing from the matrix
   - Roles need clearer definition
</methodology>

<output_format>
**RACI Matrix**:

| Activity/Decision | [Role 1] | [Role 2] | [Role 3] | [Role 4] | [Role 5] |
|-------------------|----------|----------|----------|----------|----------|
| [Activity 1]      | A        | R        | C        |          | I        |
| [Activity 2]      | I        | A        | R        | C        |          |

**Validation notes**:
- Confirmation that each row has exactly one A
- Any flagged concerns about authority alignment
- Recommended adjustments

**Role definitions**: Brief description of each role's scope and authority level

**Escalation path**: When there's disagreement between R and A, or between multiple Cs, how is it resolved?
</output_format>
