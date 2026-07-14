# Agentic Patterns

Patterns for tool use, parallel execution, long-horizon tasks, autonomy, and subagents.

## Contents

- Parallel tool calling
- Reduce over-exploration / overthinking
- Long-horizon reasoning & state tracking
- Context awareness & multi-window workflows
- State management & state files
- Autonomy & safety (confirm risky actions)
- Subagent orchestration
- Research workflows
- Prompt chaining

## Parallel tool calling

The latest models parallelize well; push to ~100% with this snippet:

```text
<use_parallel_tool_calls>
If you intend to call multiple tools and there are no dependencies between the tool calls, make all of the independent tool calls in parallel. Prioritize calling tools simultaneously whenever the actions can be done in parallel rather than sequentially. For example, when reading 3 files, run 3 tool calls in parallel to read all 3 files into context at the same time. Maximize use of parallel tool calls where possible to increase speed and efficiency. However, if some tool calls depend on previous calls to inform dependent values like the parameters, do NOT call these tools in parallel and instead call them sequentially. Never use placeholders or guess missing parameters in tool calls.
</use_parallel_tool_calls>
```

To slow down (for system stability): `Execute operations sequentially with brief pauses between each step to ensure stability.`

## Reduce over-exploration / overthinking

Higher `effort` (especially on Opus 4.6) drives more upfront exploration — usually helpful, sometimes excessive. First lever is to **lower `effort`** (see model-tuning.md). To prompt against thrashing:

```text
When you're deciding how to approach a problem, choose an approach and commit to it. Avoid revisiting decisions unless you encounter new information that directly contradicts your reasoning. If you're weighing two approaches, pick one and see it through. You can always course-correct later if the chosen approach fails.
```

Also remove blanket "be thorough / always use [tool]" defaults — they overtrigger now. Prefer "Use [tool] when it would enhance your understanding."

## Long-horizon reasoning & state tracking

The latest models track state well across extended sessions and multiple context windows. Emphasize incremental progress — steady advances on a few things at a time. Encourage full use of the context budget:

```text
This is a very long task, so it may be beneficial to plan out your work clearly. It's encouraged to spend your entire output context working on the task - just make sure you don't run out of context with significant uncommitted work. Continue working systematically until you have completed this task.
```

## Context awareness & multi-window workflows

Claude 4.6 / 4.5 models track remaining context ("token budget"). In a harness that compacts or saves state, tell the model so it does not wrap up early:

```text
Your context window will be automatically compacted as it approaches its limit, allowing you to continue working indefinitely from where you left off. Therefore, do not stop tasks early due to token budget concerns. As you approach your token budget limit, save your current progress and state to memory before the context window refreshes. Always be as persistent and autonomous as possible and complete tasks fully, even if the end of your budget is approaching. Never artificially stop any task early regardless of the context remaining.
```

For tasks spanning multiple windows: use the first window to set up a framework (tests, setup scripts); write tests in a structured file and protect them ("It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality"); create `init.sh`-style quality-of-life scripts; consider starting fresh over compaction (the models reconstruct state from the filesystem well) with prescriptive startup ("Call pwd; review progress.txt, tests.json, and git logs; run a fundamental integration test before new features"); provide verification tools (Playwright MCP, computer use) for autonomous correctness checks.

## State management & state files

- Structured data (test status) → JSON. Progress notes → freeform text. Use git as a checkpoint/log.

```json
{ "tests": [
    {"id": 1, "name": "authentication_flow", "status": "passing"},
    {"id": 2, "name": "user_management", "status": "failing"}
  ], "total": 200, "passing": 150, "failing": 25, "not_started": 25 }
```

```text
Session 3 progress:
- Fixed authentication token validation
- Next: investigate user_management test failures (test #2)
- Note: Do not remove tests as this could lead to missing functionality
```

## Autonomy & safety (confirm risky actions)

Without guidance the latest models may take hard-to-reverse actions. To require confirmation:

```text
Consider the reversibility and potential impact of your actions. You are encouraged to take local, reversible actions like editing files or running tests, but for actions that are hard to reverse, affect shared systems, or could be destructive, ask the user before proceeding.

Examples of actions that warrant confirmation:
- Destructive operations: deleting files or branches, dropping database tables, rm -rf
- Hard to reverse operations: git push --force, git reset --hard, amending published commits
- Operations visible to others: pushing code, commenting on PRs/issues, sending messages, modifying shared infrastructure

When encountering obstacles, do not use destructive actions as a shortcut. For example, don't bypass safety checks (e.g. --no-verify) or discard unfamiliar files that may be in-progress work.
```

## Subagent orchestration

The latest models delegate to subagents natively. **Opus 4.8 spawns fewer by default; Opus 4.6 may over-spawn.** Steer to the right level:

```text
Use subagents when tasks can run in parallel, require isolated context, or involve independent workstreams that don't need to share state. For simple tasks, sequential operations, single-file edits, or tasks where you need to maintain context across steps, work directly rather than delegating.
```

To encourage more fan-out (e.g. Opus 4.8): "Spawn multiple subagents in the same turn when fanning out across items or reading multiple files. Do not spawn a subagent for work you can complete directly in a single response."

## Research workflows

Define success criteria, ask for cross-source verification, and use a structured approach — see the structured-research snippet in patterns.md.

## Prompt chaining

Adaptive thinking + native orchestration handle most multi-step reasoning internally. Chain explicit API calls when you need to inspect intermediate output or enforce a pipeline. Most common pattern is **self-correction**: draft → review against criteria → refine, each as a separate call so you can log, evaluate, or branch.
