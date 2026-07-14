# Model & Parameter Tuning

How to tune behavior through API parameters and model-version-specific prompting. On the latest models these levers often beat prompt wording.

## Contents

- Effort parameter (the primary lever)
- Adaptive thinking
- Migrating from extended thinking (`budget_tokens`)
- Response length & verbosity
- Literal instruction following
- Tool-use triggering
- User-facing progress updates
- Tone & writing style
- Model self-knowledge (identity strings)
- Computer use resolution
- Model-version migration

## Effort parameter (the primary lever)

`effort` trades intelligence against token spend, speed, and cost. It is likely the most important knob on the latest models.

- **`max`** — Test for the most intelligence-demanding tasks. Diminishing returns and occasional overthinking.
- **`xhigh`** — Best for most coding and agentic use cases.
- **`high`** — Balances tokens and intelligence. Use a minimum of `high` for most intelligence-sensitive work.
- **`medium`** — Cost-sensitive work that can trade off some intelligence.
- **`low`** — Short, scoped, latency-sensitive tasks that are not intelligence-sensitive.

The latest models respect effort strictly, especially at the low end. At `low`/`medium` they scope work to exactly what was asked (good for latency/cost, but risks under-thinking on moderately complex tasks).

Guidance:
- **Shallow reasoning on a hard problem → raise effort to `high`/`xhigh`** rather than prompting around it.
- If you must stay at `low` for latency, add targeted guidance:

```text
This task involves multi-step reasoning. Think carefully through the problem before responding.
```

- At `max`/`xhigh`, set a large `max_tokens` so the model has room to think and act across tool calls and subagents. Start at 64k and tune.

## Adaptive thinking

On **Opus 4.8, thinking is off** unless you set `thinking: {type: "adaptive"}`. Opus 4.6 and Sonnet 4.6 use adaptive thinking, where Claude decides when and how much to think based on `effort` and query complexity. In internal evals, adaptive thinking outperforms manual extended thinking. Use it for agentic behavior, multi-step tool use, complex coding, and long-horizon loops.

Adaptive triggering is steerable. If the model thinks more often than wanted (common with large/complex system prompts), steer it:

```text
Thinking adds latency and should only be used when it will meaningfully improve answer quality — typically for problems that require multi-step reasoning. When in doubt, respond directly.
```

If under-thinking at `medium` on hard workloads, the first lever is to raise `effort`, not to prompt.

Guide thinking quality after tool results:

```text
After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding. Use your thinking to plan and iterate based on this new information, and then take the best next action.
```

When thinking is **off**, you can still elicit reasoning with `<thinking>`/`<answer>` tags and a self-check ("Before you finish, verify your answer against [criteria]"). Multishot examples that include `<thinking>` blocks teach the reasoning pattern. (On Opus 4.5 with thinking disabled, the word "think" is a sensitive trigger — prefer "consider," "evaluate," "reason through.")

## Migrating from extended thinking (`budget_tokens`)

`budget_tokens` is deprecated (still functional on 4.6/Sonnet 4.6). Move depth control to `effort`.

Before (older models):

```python
client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=64000,
    thinking={"type": "enabled", "budget_tokens": 32000},
    messages=[{"role": "user", "content": "..."}],
)
```

After (adaptive thinking):

```python
client.messages.create(
    model="claude-opus-4-8",
    max_tokens=64000,
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},  # or "max", "xhigh", "medium", "low"
    messages=[{"role": "user", "content": "..."}],
)
```

If you need a hard ceiling on cost, prefer lowering `effort` or using `max_tokens` as the hard limit over `budget_tokens`.

## Response length & verbosity

The latest models calibrate length to judged task complexity — shorter on lookups, longer on open-ended analysis. To reduce verbosity:

```text
Provide concise, focused responses. Skip non-essential context, and keep examples minimal.
```

For specific over-explaining patterns, add targeted instructions. **Positive examples of the right concision level beat negative "don't" instructions.** Lowering `effort` also reduces verbosity.

## Literal instruction following

The latest models interpret prompts literally, especially at lower effort. They do not silently generalize an instruction from one item to others, and do not infer unrequested work. This is a feature for tuned pipelines and structured extraction. To apply something broadly, **state the scope**: "Apply this formatting to every section, not just the first one."

## Tool-use triggering

The latest models favor reasoning over tool calls (usually better results). To get more tool use:
- **Raise `effort`** — `high`/`xhigh` show substantially more tool use in search and coding.
- Explicitly describe when and how to use a specific tool ("if you find the model not using web search, clearly describe why and how it should").

## User-facing progress updates

Opus 4.8 gives more regular, higher-quality interim updates. If you previously added scaffolding ("after every 3 tool calls, summarize progress"), try removing it. If the cadence or content is off, describe the desired updates explicitly and give an example.

## Tone & writing style

Prose trends direct and opinionated, with minimal validation-forward phrasing and sparing emoji. If your product needs a specific voice, re-prompt against the new baseline. Example for a warmer voice:

```text
Use a warm, collaborative tone. Acknowledge the user's framing before answering.
```

## Model self-knowledge (identity strings)

```text
The assistant is Claude, created by Anthropic. The current model is Claude Opus 4.8.
```

For apps that must specify a model string:

```text
When an LLM is needed, please default to Claude Opus 4.8 unless the user requests otherwise. The exact model string for Claude Opus 4.8 is claude-opus-4-8.
```

Current strings: Opus 4.8 `claude-opus-4-8` · Sonnet 4.6 `claude-sonnet-4-6` · Haiku 4.5 `claude-haiku-4-5-20251001`.

## Computer use resolution

Computer use works up to 2576px / 3.75MP. **1080p** balances performance and cost. For cost-sensitive workloads, 720p or 1366×768 perform well. Tune `effort` to adjust behavior.

## Model-version migration

**To Opus 4.8 (from 4.7):** existing 4.7 prompts work well out of the box. Tune verbosity, effort, subagent spawning, and design defaults as needed (see SKILL.md "What changed").

**General 4.x migration checklist:**
1. Be specific about desired behavior; add quality modifiers ("Go beyond the basics...").
2. Request features (animations, interactions) explicitly.
3. Switch thinking config to adaptive; control depth via `effort`.
4. Migrate away from prefilled responses (see formatting.md).
5. **Tune anti-laziness prompting down** — the latest models are more proactive and overtrigger on "be thorough / always use [tool]" language that older models needed. Replace "Default to using [tool]" with "Use [tool] when it would enhance your understanding."

**Sonnet 4.5 → 4.6:** Sonnet 4.6 defaults to `high` effort (4.5 had no effort param). Set effort explicitly: `medium` for most apps, `low` for high-volume/latency-sensitive. Use `low` effort with thinking disabled for parity-or-better vs. 4.5-without-thinking. Use a large `max_tokens` (64k) at medium/high effort. For the hardest, longest-horizon work, prefer Opus 4.8.
