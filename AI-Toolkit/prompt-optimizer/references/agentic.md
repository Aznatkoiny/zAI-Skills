# Agentic Patterns

Patterns for tool use, parallel execution, and long-running tasks.

## Parallel Tool Calling

### Maximum Parallelization

```text
<use_parallel_tool_calls>
If you intend to call multiple tools and there are no dependencies between the tool calls, make all of the independent tool calls in parallel. Prioritize calling tools simultaneously whenever the actions can be done in parallel rather than sequentially. For example, when reading 3 files, run 3 tool calls in parallel to read all 3 files into context at the same time. Maximize use of parallel tool calls where possible to increase speed and efficiency. However, if some tool calls depend on previous calls to inform dependent values like the parameters, do NOT call these tools in parallel and instead call them sequentially. Never use placeholders or guess missing parameters in tool calls.
</use_parallel_tool_calls>
```

### Reduce Parallel Execution

```text
Execute operations sequentially with brief pauses between each step to ensure stability.
```

## Multi-Context Window Workflows

### Context Awareness

```text
Your context window will be automatically compacted as it approaches its limit, allowing you to continue working indefinitely from where you left off. Therefore, do not stop tasks early due to token budget concerns. As you approach your token budget limit, save your current progress and state to memory before the context window refreshes. Always be as persistent and autonomous as possible and complete tasks fully, even if the end of your budget is approaching. Never artificially stop any task early regardless of the context remaining.
```

### Encourage Full Context Usage

```text
This is a very long task, so it may be beneficial to plan out your work clearly. It's encouraged to spend your entire output context working on the task - just make sure you don't run out of context with significant uncommitted work. Continue working systematically until you have completed this task.
```

## State Management

### Multi-Window Setup Pattern

**First context window:** Set up framework (write tests, create setup scripts).

**Subsequent windows:** Iterate on todo-list.

### Starting Fresh Instructions

```text
Call pwd; you can only read and write files in this directory.
Review progress.txt, tests.json, and the git logs.
Manually run through a fundamental integration test before moving on to implementing new features.
```

### Test Protection

```text
It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality.
```

## State File Examples

### Structured State (tests.json)

```json
{
  "tests": [
    {"id": 1, "name": "authentication_flow", "status": "passing"},
    {"id": 2, "name": "user_management", "status": "failing"},
    {"id": 3, "name": "api_endpoints", "status": "not_started"}
  ],
  "total": 200,
  "passing": 150,
  "failing": 25,
  "not_started": 25
}
```

### Progress Notes (progress.txt)

```text
Session 3 progress:
- Fixed authentication token validation
- Updated user model to handle edge cases
- Next: investigate user_management test failures (test #2)
- Note: Do not remove tests as this could lead to missing functionality
```

## Subagent Orchestration

### Conservative Subagent Usage

```text
Only delegate to subagents when the task clearly benefits from a separate agent with a new context window.
```

Claude 4.5 naturally recognizes when to delegate to subagents. Ensure subagent tools are well-defined in tool descriptions and let Claude orchestrate naturally.
