---
name: prompt-optimizer
description: Optimize prompts for Claude's latest models (Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 4.6, Haiku 4.5) using Anthropic's official prompt-engineering guidance. Use when users want to improve, refine, debug, or create prompts or system prompts for Claude. Triggers include requests to optimize/fix/refine a prompt, make a prompt more effective, write a system prompt, improve instruction following, control verbosity or output formatting, tune effort or thinking depth, fix tool-use/agentic/subagent behavior, migrate prompts to a newer Claude model, or migrate away from prefilled responses. Also use when users report Claude being too verbose, ignoring or partially applying instructions, over- or under-using tools, overthinking, overengineering, spawning too many subagents, hallucinating about code, or producing generic "AI slop" output.
---

# Prompt Optimizer

Optimize prompts for Claude's latest models — Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 4.6, Haiku 4.5 — using Anthropic's official guidance. Diagnose what is wrong, pick the right lever, apply a proven fix, then measure.

## Two levers, not one

Many problems people try to fix by editing prompt wording are better fixed with an **API parameter**. Always weigh both:

1. **Prompt** — wording, structure, examples, role, explicit scope.
2. **Parameters** — `effort` (intelligence vs. speed/cost), `thinking` (adaptive on/off), `max_tokens` (room to think and act).

On the latest models, **`effort` is frequently the highest-leverage change.** If reasoning is shallow on a hard task, raise effort to `high`/`xhigh` instead of prompting around it. If the model overthinks or over-explores, lower it. Detail in references/model-tuning.md.

## What changed for the latest models

These shifts change how to optimize. Do not carry over old habits blindly:

- **Effort governs depth, tool use, and thoroughness.** Start `xhigh` for coding/agentic work, minimum `high` for intelligence-sensitive work. Lower effort means more literal, more scoped, less tool use.
- **Thinking is off by default on Opus 4.8** unless you set `thinking: {type: "adaptive"}`. Opus 4.6 and Sonnet 4.6 use adaptive thinking. `budget_tokens` is deprecated — control depth through `effort`.
- **Literal instruction following.** The model does what you said, not what you implied. State scope explicitly ("apply to every section, not just the first one").
- **Dial back anti-laziness prompting.** Aggressive "CRITICAL / You MUST" language needed for older models now causes overtriggering. Use normal phrasing ("Use this tool when...").
- **Prefilled assistant responses are no longer supported** on 4.6+ models (the request returns a 400). Migrations in references/formatting.md.
- **Verbosity is calibrated to task complexity** and prose is more direct. Tune with positive examples of the concision you want, not "don't" rules.
- **Fewer subagents by default** on Opus 4.8. Steer explicitly when you want fan-out.

## Optimization workflow

1. **Diagnose** the symptom (use the routing table below).
2. **Choose the lever** — a parameter (effort / thinking / max_tokens) and/or a prompt change.
3. **Apply** the fix — pull a snippet from the references, or adjust the parameter.
4. **Be explicit and positive** — say what TO do, give the reason, state the scope, prefer positive examples over negative rules.
5. **Measure** against real cases or an eval subset, then iterate. Never assume a prompt change helped without checking.

## Symptom → fix routing

| Symptom | First lever | Reference |
|---|---|---|
| Too verbose / over-explains | Positive concision example; lower effort | model-tuning.md, formatting.md |
| Shallow reasoning on hard task | Raise effort to high/xhigh | model-tuning.md |
| Overthinks / over-explores / slow | Lower effort; "commit to an approach" snippet | model-tuning.md, agentic.md |
| Ignores or partially applies an instruction | Make explicit; state scope; positive framing | core principles below |
| Too much markdown / bullets | Prose-first snippet; match prompt style | formatting.md |
| Outputs LaTeX, want plain text | Plain-text math snippet | formatting.md |
| Will not take action (only suggests) | Explicit imperative; default_to_action | patterns.md |
| Over- or under-uses tools | Adjust effort; explicit tool guidance; dial back "MUST" | patterns.md, model-tuning.md |
| Not parallelizing tool calls | use_parallel_tool_calls snippet | agentic.md |
| Spawns too many / too few subagents | Explicit subagent guidance | agentic.md |
| Overengineers / extra files & abstractions | Anti-overengineering snippet | patterns.md |
| Hardcodes to pass tests | General-solution snippet | patterns.md |
| Hallucinates about code | investigate_before_answering snippet | patterns.md |
| Risky autonomous actions | Reversibility / confirmation snippet | agentic.md |
| Loses state over long or multi-window tasks | Context-awareness + state-file patterns | agentic.md |
| Code-review harness misses bugs | Coverage-not-filter snippet | patterns.md |
| Generic "AI slop" frontend | Concrete spec or propose-options-first; aesthetics snippet | frontend-design.md |
| Was relying on prefill | Migrate to structured outputs / instructions | formatting.md |
| Moving to a newer Claude model | Update thinking config; tune anti-laziness | model-tuning.md |

## Core principles (apply to every prompt)

1. **Be clear and direct.** Specify the desired output, format, and constraints. Want "above and beyond"? Ask for it explicitly. *Golden rule: if a colleague with no context would be confused by the prompt, so will Claude.*
   - Less: `Create an analytics dashboard`
   - More: `Create an analytics dashboard. Include as many relevant features and interactions as possible. Go beyond the basics to create a fully-featured implementation.`
2. **Give the reason.** Motivation lets Claude generalize correctly.
   - Less: `NEVER use ellipses`
   - More: `Your response will be read aloud by a text-to-speech engine, so never use ellipses since it will not know how to pronounce them.`
3. **Use examples (3–5).** Make them relevant, diverse, and wrapped in `<example>` tags. Examples steer format and tone better than description.
4. **Structure with XML tags.** Use `<instructions>`, `<context>`, `<input>` — consistent, descriptive names, nested when the content is hierarchical.
5. **Give a role** in the system prompt — even one sentence shifts tone and focus.
6. **State scope explicitly.** The latest models are literal: "every section, not just the first."
7. **Say what TO do, not what NOT to do.** Positive framing and positive examples outperform prohibitions.
8. **Long context:** put long documents at the top, above the query; wrap each in `<document>` tags; ask for relevant quotes first.

## Reference files

Read the file that matches the optimization need:

- **references/model-tuning.md** — effort levels, adaptive thinking, verbosity, literal instruction following, tone, model identity, computer use, and model-version migration. Read this for any parameter or model-version question.
- **references/patterns.md** — copy-paste snippet library: action defaults, tool triggering, hallucination prevention, overengineering, hardcoding, research, code-review harnesses, progress updates.
- **references/formatting.md** — output format and verbosity control, LaTeX, document creation, and prefill migration.
- **references/agentic.md** — long-horizon reasoning and state, context awareness, multi-window workflows, autonomy & safety, subagents, parallel tools, prompt chaining.
- **references/frontend-design.md** — overriding the Opus 4.8 design defaults, frontend-aesthetics snippets, and vision / crop-tool tips.
