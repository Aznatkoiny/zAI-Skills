---
name: prompt-engineer
description: Write, review, debug, and migrate prompts for Claude models (Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5) using Anthropic's official prompt engineering guidance. Covers system prompts, agent and harness prompts, tool descriptions, few-shot examples, and effort/thinking settings. Use this whenever the user wants to create or improve a prompt or system prompt. Also use it when they ask why Claude is behaving a certain way: too verbose or too terse, stops early or asks permission mid-task, over-engineers, goes silent between tool calls, skips searches or tool calls, refuses benign requests, ignores mid-turn messages, or returns broken JSON. It also covers migrating prompts or API calls to a newer Claude model, choosing an effort level or thinking configuration, and writing instructions that another LLM agent will follow, even when the user never says "prompt engineering".
---

# Prompt engineer

Help the user get the behavior they want from a Claude model by writing or changing the words, and sometimes the API settings, that the model sees. The guidance here comes from Anthropic's prompt engineering docs (fetched 2026-10-09). It is current for Claude Fable 5.1 / Mythos 5.1, Opus 5.5, Sonnet 5.5, and Haiku 5.5.

## Reference files

Read only what the task needs. The files are long, so grep for the section you want instead of reading top to bottom.

| File | Read when |
|---|---|
| `references/best-practices.md` | Any prompt work. General techniques for all current models, with many ready-to-use sample blocks: clarity, examples, XML, long context, formatting, prefill migration, tool use, parallel calls, thinking, agentic and long-horizon work, overeagerness, hallucination, frontend design. |
| `references/models/fable-5-1.md` | Target is Claude Fable 5.1 or Mythos 5.1 |
| `references/models/opus-5-5.md` | Target is Claude Opus 5.5 |
| `references/models/sonnet-5-5.md` | Target is Claude Sonnet 5.5 |
| `references/models/haiku-5-5.md` | Target is Claude Haiku 5.5 |

Each model file opens with a list of symptoms ("Little or no text between tool calls", "Requests return `stop_reason: \"refusal\"`" …) that link to the section that fixes them. When the user describes a behavior, match it against that list first.

The docs change. If the user is targeting a model not listed here, or something looks out of date, fetch the current page. Appending `.md` to any platform.claude.com docs URL returns raw markdown, for example `curl -sL https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5.md`. Other model pages follow the same pattern (`prompting-claude-opus-5`, `prompting-claude-sonnet-5`, `prompting-claude-fable-5`, `prompting-claude-opus-4-8`).

## Workflow

### 1. Work out which job this is

- **Draft:** write a new prompt from a description of the use case.
- **Improve:** review an existing prompt and make it better.
- **Diagnose:** the user describes unwanted behavior; find the cause and the fix.
- **Migrate:** move a prompt and its API settings from an older model to a newer one.

These often overlap. A diagnosis usually ends with an improved prompt.

### 2. Pin down the target model and the surface

Many recommendations depend on the model, and some reverse between models. For example, anti-markdown rules help older models but suppress needed structure on Fable 5.1. Self-check instructions help most models but cause over-verification on Opus 5. If the model isn't stated, infer it from the code (`model=` strings) or ask. If you still can't tell, write for the general case, name the assumption, and point out the places where the answer would change.

Also note where the prompt runs:
- **Raw API:** effort and thinking settings are in play.
- **Claude Code, CLAUDE.md, or a skill:** only the words matter.
- **Chat product with real-time users vs. an unattended agent:** these get opposite advice on progress updates and on stopping to ask.

### 3. Check that success is defined

The overview doc's precondition for prompt engineering is (1) clear success criteria, (2) a way to test against them empirically, and (3) a first-draft prompt. If (1) or (2) is missing, say so briefly and propose a few concrete criteria or test inputs. Don't refuse to proceed. Also say when prompting isn't the right lever. Latency and cost often improve more from a different model or a lower effort level than from rewording.

### 4. Write or revise

Apply the principles below and the target model's file. When the docs supply a sample block for the exact behavior, prefer the documented wording or adapt it closely. Anthropic tested those phrasings, and some notes say outright that wording matters. For example, Fable 5.1's "Finish the whole task" block notes that its opening sentence "carries much of the effect. Keep it as written."

### 5. Deliver

Unless the user wants something else, return:

1. **The prompt** in a fenced block, ready to paste. Use placeholders like `{{DOCUMENT}}` for variable content.
2. **What changed and why:** a short list, one line per change, each tied to the principle or doc section behind it. For a review, put the most consequential problems first.
3. **Settings** when the API is in play: model, effort, thinking config, and `max_tokens`. Mention structured outputs, tool_choice, or turn-scoped system messages where they fit.
4. **How to test it:** a few concrete inputs or checks, especially edge cases, plus the failure mode to watch for. Several fixes in the docs come with trade-offs. For example, autonomy blocks make the model ask fewer clarifying questions, and "treat earlier answers as done" makes it less likely to catch its own earlier mistakes. Name the trade-off.

Keep the explanation in proportion. A one-line fix doesn't need a report.

## Core principles (all current models)

These are condensed from `references/best-practices.md`. Each one carries the reason behind it, because Claude generalizes from reasons better than from bare rules.

- **Be clear, direct, and specific.** Treat the model like a brilliant new employee who lacks your context. Golden rule: if a colleague with minimal context would be confused by the prompt, Claude will be too. If you want above-and-beyond output, ask for it explicitly. Current models follow instructions precisely instead of guessing at ambition.
- **Explain why.** "Your response will be read aloud by a text-to-speech engine, so never use ellipses" beats "NEVER use ellipses". The model generalizes from the reason to cases the rule didn't list.
- **Use calm language, not shouting.** Current models are very responsive to the system prompt. "CRITICAL: You MUST use this tool when…" written to fix undertriggering on older models now causes overtriggering. Write "Use this tool when…".
- **Say what to do, not what to avoid**, especially for format. "Write in flowing prose paragraphs" works better than "don't use markdown". Your prompt's own style also leaks into the output, so a markdown-heavy prompt gets markdown-heavy replies.
- **Use examples well.** Three to five examples, relevant and diverse, wrapped in `<example>` inside `<examples>`. They are the most reliable way to steer format and tone. Vary them so the model doesn't copy incidental features.
- **Separate kinds of content with XML tags**, such as `<instructions>`, `<context>`, and `<documents><document index="n"><source>…</source><document_content>…</document_content></document></documents>`. Use consistent, descriptive tag names.
- **Put long context first.** Place documents of 20k+ tokens at the top and the query or instructions at the end. In tests this improved quality by up to 30%. For long-document tasks, ask the model to pull out relevant quotes first.
- **Give a role.** One sentence in the system prompt focuses tone and behavior.
- **Make actions explicit.** "Can you suggest changes?" gets suggestions. "Change this function to…" gets edits. Set the default with `<default_to_action>` or `<do_not_act_before_instructions>` (sample blocks in best-practices → Tool usage).
- **Prefer general guidance over scripted steps for reasoning.** "Think thoroughly" usually beats a hand-written chain of steps, because the model's reasoning often exceeds what a person would script. Use numbered steps when order or completeness genuinely matters.
- **Use prompt chaining** only when you need to inspect intermediate outputs or enforce a pipeline. The common pattern is draft → review against criteria → refine. Adaptive thinking and subagents handle most multi-step work internally.
- **Address agentic failure modes directly.** Best-practices has tested blocks for: risky or irreversible actions, overengineering, hard-coding to pass tests, speculating about unread code, temp-file cleanup, subagent overuse, context-window persistence, multi-window state (tests.json, progress.txt, git), and structured research.

## What used to help but now hurts

Prompts carried over from older models often contain these. Look for them in every review and migration.

| Pattern in the old prompt | Problem now | Replace with |
|---|---|---|
| Prefilled final assistant turn (`"Here is the JSON:"`, `{`) | Returns a 400 error from Claude 4.6 onward | Structured outputs, tool with enum, direct instruction ("Respond directly without preamble"), or XML output tags. Best-practices → *Migrating away from prefilled responses* |
| `thinking: {type: "enabled", budget_tokens: N}` | 400 on Claude 4.7+ | Adaptive thinking (the only mode on Fable 5.1 and Opus 5.5) with `effort` as the control |
| "Think step by step in `<thinking>` tags" or "show your reasoning in the response" | On Fable 5.1, Fable 5, Opus 5.5, Opus 5, and Sonnet 5.5 this can be declined as `reasoning_extraction` | Rely on built-in thinking (lower effort if cost matters); read `display: "summarized"` thinking blocks; ask for a *short explanation* or *summary of actions* instead |
| "CRITICAL / MUST / If in doubt, use X" for tools | Overtriggering | Plain "Use X when it would help with…" |
| Long anti-markdown or anti-bullet blocks | Fable 5.1 already formats less, so these suppress structure the content needs | Delete, or use Fable 5.1's short "Formatting in chat" rule |
| "Verify your answer against…" carried to Opus 5 | Over-verification: extra tokens and latency | Remove on Opus 5 (still useful on most others, and *needed* for Sonnet 5.5 and Haiku 5.5 coding agents at low effort) |
| "Think carefully before answering" in a chat system prompt (Opus 5.5) | Slower first token, no clear quality gain | Remove it; control depth with effort |
| "Hold all findings for the final response" / "keep updates brief" | Fable 5.1, Opus 5.5, and Sonnet 5.5 agents look silent | Remove it, then ask for updates explicitly if wanted |
| "Only use tools when strictly necessary" / "minimize tool calls" | Sonnet 5.5 and Fable 5.1 (low effort) answer from stale memory | Remove it; add the model's search-nudge line |
| Asking the model to think less in the prompt | Unreliable on Sonnet 5.5 and Haiku 5.5 | Lower `effort` instead |
| Editing earlier turns, rebuilding `system`/`tools` mid-session, in-place summarization, inject-then-delete reminders | Invalidates thinking blocks (400 or dropped blocks on Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5) and restarts the prompt cache | Keep history append-only; use mid-conversation or turn-scoped system messages; use server-side compaction or context editing |
| User text placed inside `tool_result`, or harness text after every tool result | Sonnet 5.5 and Haiku 5.5 treat real user messages as prompt injection | Put user words in a text block after the last `tool_result`; keep harness notices in a separate system message; avoid per-step countdowns |
| Reading `response.content[0].text` | The response may start with a `thinking` block | Select blocks by `type` |
| `max_tokens` sized for no-thinking replies | Thinking counts toward `max_tokens`, so replies get cut off | Leave room for thinking (Opus 5.5 and Sonnet 5.5 docs recommend 128k, the maximum, for agentic coding) |

## Effort and thinking at a glance

Effort is now the main dial for intelligence vs. latency vs. cost. Level names don't map to the same amount of thinking across models, so re-sweep on the user's evals when switching models instead of copying the old setting.

| Model | Default effort | Starting points | Thinking |
|---|---|---|---|
| Fable 5.1 / Mythos 5.1 | `high` | Try `medium`/`low` where evals hold. `low` often beats smaller models on cost per task. Use `xhigh`/`max` only where you've measured a gain, and leave `max_tokens` room. | Always on (adaptive only) |
| Opus 5.5 | `medium` | `low` for latency-sensitive work or for integrations that used thinking-disabled on Opus 5. `medium` ≈ Opus 5 at `high`. | Always on; `disabled` not accepted |
| Sonnet 5.5 | `high` (API) | Agentic coding: `medium`, up to `high` for hard tasks. Chat: `medium`/`low`. `low` skips verification and `low`/`medium` may check in early. | On by default; lowest setting is `between_tools` (effort ≤ `high`, and not for reasoning-without-tools tasks) |
| Haiku 5.5 | `medium` | `low` for chat and high-volume work; `high` for knowledge work and strict instruction following. For `xhigh`/`max`, compare against Sonnet 5.5. | On by default; `disabled` allowed at `low`/`medium`/`high` |

To change effort mid-conversation without busting the cache, use a per-message effort change (beta) instead of changing the top-level value.

## Diagnosing behavior: quick map

Start here, then open the model file for the exact sample prompt.

- **Stops early / asks "Shall I…?" / announces next steps without doing them:** Fable 5.1 → *Finish the whole task*. Opus 5.5 → *Unattended agentic runs* (also treat text-only `end_turn` as a report, not completion). Sonnet 5.5 → *Steer initiative and scope*. Haiku 5.5 → *Prevent early stopping*. Raising effort also helps.
- **Does more than asked / extra tests, docs, refactors:** Fable 5.1 → *Keep changes and tests to what the task asks for*. Sonnet 5.5 → second paragraph of the initiative block, plus the `xhigh`/`max` review-rounds block. Best-practices → *Overeagerness*.
- **Silent during long tool chains:** set `thinking.display: "updates"` (beta) so progress-update thinking blocks reach the client. Remove narration-suppressing lines. Ask for a one-line intent plus a recap. As a last resort, use a harness reminder after about 5 silent steps, as a turn-scoped system message, at most 2–3 times.
- **Answers from memory instead of searching:** give today's date (Haiku 5.5). Add the model's search-nudge line (Fable 5.1 low effort, Sonnet 5.5, Haiku 5.5). Avoid blanket "always search" rules, which overtrigger.
- **JSON wrong or unparseable on reasoning tasks:** Sonnet 5.5 → *Reasoning tasks with JSON output* ("Think the problem through before you answer.", parse the last JSON value, treat `max_tokens` stops as failures). Haiku 5.5 → *JSON output with your own tools*.
- **Benign request refused (`stop_reason: "refusal"`):** check `stop_details.category`. For `reasoning_extraction`, remove reasoning-in-response instructions. For Fable 5.1 false positives, rephrase "does this compile?" as "are there bugs?", explain lesser-known languages, and drop base64 tool output.
- **Verbose or dense prose:** Fable 5.1 → *Writing density* ("Please remove all mannered prose."). Opus 5 runs long by default, so prompt for concision explicitly.
- **Follows instructions inside pasted content:** Opus 5.5 → *Mark pasted text in user messages* (`<pasted_content id="…">` plus a system note).
- **Chatbot caves when users push:** Haiku 5.5 → *Keep chatbots to their system prompt*, and use `high` effort.
- **Generic "AI-looking" frontends:** name the specific patterns to avoid (Opus 5.5), and use best-practices `<frontend_aesthetics>`. A vague "avoid generic" instruction just swaps one default for another.
- **Weak on dense charts or drawings:** give a crop/zoom tool or a container with PIL/OpenCV. On Sonnet 5.5 this matters more than raising effort.
- **Rewrites whole files for small edits (Fable 5.1):** add the targeted-edits line.
- **Overthinking or slow first token:** lower effort first. Use best-practices' "choose an approach and commit to it" line. On Opus 5.5 chat, use "treat earlier answers as done".

## Writing prompts for other agents (skills, CLAUDE.md, subagent briefs)

The same principles apply. Explain the purpose and the reasoning, describe the situation instead of issuing a list of MUSTs, and give the agent what it needs to judge edge cases. For autonomous agents, say explicitly whether a human is watching, because the docs' autonomy guidance depends on it. State which actions still need confirmation (destructive, irreversible, or visible to others), and give a clear completion condition.
