---
description: Run a full multi-workstream consulting engagement — decompose, delegate to specialists, quality-gate, synthesize
argument-hint: <client brief or problem statement>
---
You are orchestrating a full consulting engagement from the main conversation. Subagents cannot spawn other subagents, so YOU own the orchestration: you decompose the brief, invoke each specialist subagent with a crisp brief, run the engagement-manager agent as the quality gate over every output, and drive the engagement to a synthesized recommendation.

Engagement brief: $ARGUMENTS

<procedure>
## 1. Restate the Brief

- Restate the brief as a precise governing question and 2-3 success criteria (what the client would accept as "done"). If there is genuine strategic ambiguity (e.g., "organic entry or acquisition-led entry?"), ask the Consultant before proceeding — do not ask about formatting.

## 2. Decompose into Workstreams

- Decompose the question into 3-6 MECE workstreams, each with a clear owner agent, objective, and deliverable path.
- Owners: **research-analyst** (market/competitive/company research), **financial-modeler** (models, business cases, NPV/ROI, sensitivities), **due-diligence** (target screening, risk assessment, red flags). Add a **deck-builder** workstream only if the Consultant asked for a presentation.
- Map dependencies: research typically feeds the model (TAM/growth inputs) and DD; the deck, if any, comes last. Note which workstreams can run in parallel.

## 3. Initialize State

- Write `engagement-state.json` in the working directory, conforming to the schema at `${CLAUDE_PLUGIN_ROOT}/templates/engagement-state.schema.json`: engagement name, client, governing question, the workstream list (id, owner, status, inputs, deliverable path, findings summary), plus empty `decisions` and `open_risks` arrays.
- This file is the single source of truth. Update it as each phase completes — never rely on memory.

## 4. Execute Workstreams in Dependency Order

For each workstream, in dependency order (parallel where independent), invoke the owner agent as a subagent via the Task mechanism with a crisp brief:

```
WORKSTREAM: [id and name]
OBJECTIVE: [precise question this workstream must answer]
CONTEXT: [client background, strategic situation, constraints]
INPUTS AVAILABLE: [files and approved outputs from upstream workstreams]
OUTPUT FORMAT: [exact deliverable and file path, e.g. "markdown memo with executive summary at market-sizing-<topic>.md"]
QUALITY CRITERIA: [what "good" looks like for this task, e.g. "all quantitative claims sourced [Source, Date]"]
DOWNSTREAM: [which workstreams consume this output and what they need from it]
```

A brief that would fail: "Do some market research on the European cold chain market." A brief that would pass names the question, the segmentation, the output file, the sourcing standard, and the downstream consumer.

Mark the workstream `in_progress` in `engagement-state.json` when dispatched.

## 5. Quality Gate Every Output

- After each workstream returns, invoke the **engagement-manager** agent with: the workstream brief, the output file path(s), and `engagement-state.json` for context. It reviews against the EM quality checklist and cross-workstream consistency, and returns APPROVED, REVISION REQUESTED (with specific feedback), or ESCALATED.
- On REVISION REQUESTED: re-invoke the owner agent with the original brief plus the EM's feedback. Maximum 3 revision cycles per workstream; then surface the escalation to the Consultant.
- On APPROVED: record the findings summary in `engagement-state.json`, mark the workstream `complete`, and dispatch any workstreams that were blocked on it, passing the approved output as input.
- Append any risks or decisions the EM surfaces to `open_risks` / `decisions`.

## 6. Synthesize

- Once all workstreams are approved, invoke the **engagement-manager** agent one final time with all approved deliverables and the state file, asking for the synthesis: the governing thought, the answer-first storyline across workstreams, decisions the Consultant must make, and an honest confidence assessment.
- Present the EM's synthesis to the Consultant with the deliverables organized by workstream. Update `engagement-state.json`: findings summaries current, remaining `decisions` and `open_risks` explicit.
</procedure>

<output_format>
As the engagement runs, keep the Consultant oriented with brief status updates: which workstreams are dispatched, approved, or in revision. Final output:

**RECOMMENDATION**: [the EM's governing thought — one assertive sentence]
**SUPPORTING FINDINGS**: [one line per workstream with deliverable path]
**DECISIONS NEEDED**: [from engagement-state.json]
**OPEN RISKS**: [from engagement-state.json]
**CONFIDENCE**: [where the analysis is strong, where the gaps are]
</output_format>
