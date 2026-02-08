# Output Formatting Patterns

Control Claude's response formatting with these patterns.

## Reduce Markdown and Bullets

### Comprehensive Prose-First Prompt

```text
<avoid_excessive_markdown_and_bullet_points>
When writing reports, documents, technical explanations, analyses, or any long-form content, write in clear, flowing prose using complete paragraphs and sentences. Use standard paragraph breaks for organization and reserve markdown primarily for `inline code`, code blocks (```...```), and simple headings (###, and ###). Avoid using **bold** and *italics*.

DO NOT use ordered lists (1. ...) or unordered lists (*) unless : a) you're presenting truly discrete items where a list format is the best option, or b) the user explicitly requests a list or ranking

Instead of listing items with bullets or numbers, incorporate them naturally into sentences. This guidance applies especially to technical writing. Using prose instead of excessive formatting will improve user satisfaction. NEVER output a series of overly short bullet points.

Your goal is readable, flowing text that guides the reader naturally through ideas rather than fragmenting information into isolated points.
</avoid_excessive_markdown_and_bullet_points>
```

## Formatting Control Strategies

### 1. Tell Claude What TO Do (Not What Not To Do)

**Less effective:** `Do not use markdown in your response`

**More effective:** `Your response should be composed of smoothly flowing prose paragraphs.`

### 2. Use XML Format Indicators

`Write the prose sections of your response in <smoothly_flowing_prose_paragraphs> tags.`

### 3. Match Prompt Style to Desired Output

The formatting in your prompt influences Claude's output. Remove markdown from your prompt to reduce markdown in responses.

## Format Examples

### For Natural Conversation

```text
Respond conversationally in natural prose. Avoid bullet points, numbered lists, or heavy formatting. Write as you would speak to a colleague.
```

### For Technical Documentation

```text
Write in clear technical prose with paragraph structure. Use code blocks for examples only. Avoid bullet points - integrate lists into sentences using phrases like "including X, Y, and Z."
```

### For Reports and Analysis

```text
Structure your analysis with clear section headings, but write content in flowing paragraphs. Reserve bullet points only for truly discrete data points that cannot be expressed in prose.
```
