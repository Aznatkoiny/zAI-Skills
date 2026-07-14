# Output Formatting & Verbosity Control

Control the structure, format, and verbosity of Claude's responses.

## Contents

- Four formatting-control strategies
- Reduce markdown and bullets (prose-first)
- Format examples by use case
- Plain-text math (no LaTeX)
- Document creation
- Migrating away from prefilled responses

## Four formatting-control strategies

1. **Tell Claude what TO do, not what NOT to do.**
   - Less: `Do not use markdown in your response`
   - More: `Your response should be composed of smoothly flowing prose paragraphs.`
2. **Use XML format indicators.** `Write the prose sections of your response in <smoothly_flowing_prose_paragraphs> tags.`
3. **Match prompt style to desired output.** The formatting of your prompt influences the output. Removing markdown from the prompt reduces markdown in responses.
4. **Be explicit for specific preferences** — use the detailed prose-first snippet below.

## Reduce markdown and bullets (prose-first)

```text
<avoid_excessive_markdown_and_bullet_points>
When writing reports, documents, technical explanations, analyses, or any long-form content, write in clear, flowing prose using complete paragraphs and sentences. Use standard paragraph breaks for organization and reserve markdown primarily for `inline code`, code blocks (```...```), and simple headings (###, and ###). Avoid using **bold** and *italics*.

DO NOT use ordered lists (1. ...) or unordered lists (*) unless : a) you're presenting truly discrete items where a list format is the best option, or b) the user explicitly requests a list or ranking

Instead of listing items with bullets or numbers, incorporate them naturally into sentences. This guidance applies especially to technical writing. Using prose instead of excessive formatting will improve user satisfaction. NEVER output a series of overly short bullet points.

Your goal is readable, flowing text that guides the reader naturally through ideas rather than fragmenting information into isolated points.
</avoid_excessive_markdown_and_bullet_points>
```

## Format examples by use case

Natural conversation:

```text
Respond conversationally in natural prose. Avoid bullet points, numbered lists, or heavy formatting. Write as you would speak to a colleague.
```

Technical documentation:

```text
Write in clear technical prose with paragraph structure. Use code blocks for examples only. Avoid bullet points - integrate lists into sentences using phrases like "including X, Y, and Z."
```

Reports and analysis:

```text
Structure your analysis with clear section headings, but write content in flowing paragraphs. Reserve bullet points only for truly discrete data points that cannot be expressed in prose.
```

## Plain-text math (no LaTeX)

The latest models default to LaTeX for math. For plain text:

```text
Format your response in plain text only. Do not use LaTeX, MathJax, or any markup notation such as \( \), $, or \frac{}{}. Write all math expressions using standard text characters (e.g., "/" for division, "*" for multiplication, and "^" for exponents).
```

## Document creation

The latest models produce polished presentations, animations, and visual documents on the first try. Request design intent explicitly:

```text
Create a professional presentation on [topic]. Include thoughtful design elements, visual hierarchy, and engaging animations where appropriate.
```

## Migrating away from prefilled responses

Prefilled assistant messages on the **last** turn are unsupported on Claude 4.6+ (returns 400). Adding assistant messages elsewhere in the conversation is unaffected. Migrate by scenario:

- **Forcing output format (JSON/YAML/classification):** use [Structured Outputs](https://docs.claude.com/en/docs/build-with-claude/structured-outputs) with a schema, or just ask for the structure (the latest models match complex schemas reliably, especially with retries). For classification, use a tool with an enum field or structured outputs.
- **Eliminating preambles** (`Here is the summary:\n`): instruct in the system prompt — "Respond directly without preamble. Do not start with phrases like 'Here is...', 'Based on...'." Or emit inside XML tags / via a tool. Strip stray preambles in post-processing.
- **Avoiding bad refusals:** no longer needed — clear prompting in the user message suffices.
- **Continuations:** move the continuation to the user turn and include the interrupted text: "Your previous response was interrupted and ended with `[previous_response]`. Continue from where you left off." Or retry the request.
- **Context hydration / role consistency:** inject what were prefilled reminders into the user turn, hydrate via tools, or refresh during context compaction.
