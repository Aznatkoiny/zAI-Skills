# Prompt Patterns Reference

Copy-paste-ready prompt snippets for common optimization needs. Use the snippet, then adapt scope/wording to the use case.

## Contents

- Taking action (proactive vs. conservative)
- Tool triggering & dialing back over-prompting
- Investigate before answering (anti-hallucination)
- General-purpose solutions (anti-hardcoding)
- Anti-overengineering
- Clean up temporary files
- Code-review harnesses (coverage vs. filter)
- Structured research
- Progress updates after tool use

## Taking action (proactive vs. conservative)

The latest models follow instructions literally: "suggest changes" yields suggestions, not edits. Be explicit about whether to act. "Change this function..." / "Make these edits..." trigger action; "Can you suggest..." does not.

Proactive by default:

```text
<default_to_action>
By default, implement changes rather than only suggesting them. If the user's intent is unclear, infer the most useful likely action and proceed, using tools to discover any missing details instead of guessing. Try to infer the user's intent about whether a tool call (e.g., file edit or read) is intended or not, and act accordingly.
</default_to_action>
```

Conservative by default:

```text
<do_not_act_before_instructions>
Do not jump into implementation or change files unless clearly instructed to make changes. When the user's intent is ambiguous, default to providing information, doing research, and providing recommendations rather than taking action. Only proceed with edits, modifications, or implementations when the user explicitly requests them.
</do_not_act_before_instructions>
```

## Tool triggering & dialing back over-prompting

The latest models are more responsive to the system prompt and **overtrigger** on aggressive language. If a tool or skill fires too often, dial back:
- Replace `CRITICAL: You MUST use this tool when...` with `Use this tool when...`.
- Replace `Default to using [tool]` / `If in doubt, use [tool]` with `Use [tool] when it would enhance your understanding of the problem.`

To *increase* tool use, prefer raising `effort` (see model-tuning.md); if prompting, describe exactly when and how to use the specific tool.

## Investigate before answering (anti-hallucination)

```text
<investigate_before_answering>
Never speculate about code you have not opened. If the user references a specific file, you MUST read the file before answering. Make sure to investigate and read relevant files BEFORE answering questions about the codebase. Never make any claims about code before investigating unless you are certain of the correct answer - give grounded and hallucination-free answers.
</investigate_before_answering>
```

## General-purpose solutions (anti-hardcoding)

Use when the model games tests or builds workarounds instead of solving the problem.

```text
Please write a high-quality, general-purpose solution using the standard tools available. Do not create helper scripts or workarounds to accomplish the task more efficiently. Implement a solution that works correctly for all valid inputs, not just the test cases. Do not hard-code values or create solutions that only work for specific test inputs. Instead, implement the actual logic that solves the problem generally.

Focus on understanding the problem requirements and implementing the correct algorithm. Tests are there to verify correctness, not to define the solution. Provide a principled implementation that follows best practices and software design principles.

If the task is unreasonable or infeasible, or if any of the tests are incorrect, please inform me rather than working around them. The solution should be robust, maintainable, and extendable.
```

## Anti-overengineering

Use when the model adds unrequested files, abstractions, or flexibility.

```text
Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused:

- Scope: Don't add features, refactor code, or make "improvements" beyond what was asked. A bug fix doesn't need surrounding code cleaned up. A simple feature doesn't need extra configurability.

- Documentation: Don't add docstrings, comments, or type annotations to code you didn't change. Only add comments where the logic isn't self-evident.

- Defensive coding: Don't add error handling, fallbacks, or validation for scenarios that can't happen. Trust internal code and framework guarantees. Only validate at system boundaries (user input, external APIs).

- Abstractions: Don't create helpers, utilities, or abstractions for one-time operations. Don't design for hypothetical future requirements. The right amount of complexity is the minimum needed for the current task.
```

## Clean up temporary files

```text
If you create any temporary new files, scripts, or helper files for iteration, clean up these files by removing them at the end of the task.
```

## Code-review harnesses (coverage vs. filter)

The latest models find more bugs but **follow self-filtering instructions faithfully** — "only report high-severity" can lower measured recall even as bug-finding improves. Split finding from filtering. At the finding stage, prompt for coverage:

```text
Report every issue you find, including ones you are uncertain about or consider low-severity. Do not filter for importance or confidence at this stage - a separate verification step will do that. Your goal here is coverage: it is better to surface a finding that later gets filtered out than to silently drop a real bug. For each finding, include your confidence level and an estimated severity so a downstream filter can rank them.
```

If self-filtering in a single pass, make the bar concrete instead of qualitative ("important"): e.g., "report any bugs that could cause incorrect behavior, a test failure, or a misleading result; only omit nits like pure style or naming preferences." Validate recall/F1 against an eval subset.

## Structured research

```text
Search for this information in a structured way. As you gather data, develop several competing hypotheses. Track your confidence levels in your progress notes to improve calibration. Regularly self-critique your approach and plan. Update a hypothesis tree or research notes file to persist information and provide transparency. Break down this complex research task systematically.
```

## Progress updates after tool use

The latest models may skip verbal summaries and jump to the next action. To restore visibility:

```text
After completing a task that involves tool use, provide a quick summary of the work you've done.
```
