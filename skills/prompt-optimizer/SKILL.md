---
name: prompt-optimizer
description: Optimize prompts for Claude 4.x models using Anthropic's official best practices. Use when users want to improve, refine, or create effective prompts for Claude. Triggers include requests to optimize prompts, make prompts more effective, fix underperforming prompts, create system prompts, improve instruction following, reduce verbosity, control output formatting, or enhance agentic/tool-use behaviors. Also use when users report Claude is being too verbose, not following instructions, not using tools properly, or producing generic outputs.
---

# Prompt Optimizer

Optimize prompts for Claude 4.x models (Sonnet 4.5, Haiku 4.5, Opus 4.5) using Anthropic's official guidance.

## Core Principles

### 1. Be Explicit

Claude 4.x models follow instructions precisely. Request behaviors explicitly rather than hoping Claude infers them.

**Less effective:** `Create an analytics dashboard`

**More effective:** `Create an analytics dashboard. Include as many relevant features and interactions as possible. Go beyond the basics to create a fully-featured implementation.`

### 2. Provide Context for Why

Explain motivation behind instructions to help Claude generalize appropriately.

**Less effective:** `NEVER use ellipses`

**More effective:** `Your response will be read aloud by a text-to-speech engine, so never use ellipses since the text-to-speech engine will not know how to pronounce them.`

### 3. Align Examples with Desired Behavior

Claude pays close attention to examples. Ensure they demonstrate exactly what you want, without patterns you want to avoid.

## Optimization Workflow

1. **Diagnose** the issue (verbosity, formatting, tool use, instruction following)
2. **Select** relevant patterns from references/patterns.md
3. **Apply** the appropriate prompt snippets
4. **Test** the optimized prompt

## Quick Fixes by Issue

### Too Verbose
Add: `Keep responses concise and direct. Avoid unnecessary elaboration.`

### Too Much Markdown/Bullets
See references/formatting.md for detailed prompts to control output style.

### Not Using Tools
Add: `By default, implement changes rather than only suggesting them. Use tools to take action.`

### Generic "AI Slop" Output
Add creativity guidance or use the frontend-aesthetics pattern from references/patterns.md.

### Not Following Instructions
Make instructions explicit, add context for why, frame positively (what TO do, not what NOT to do).

## Reference Files

- **references/patterns.md** - Complete prompt snippets organized by use case
- **references/formatting.md** - Output format control patterns
- **references/agentic.md** - Tool use, parallel execution, and multi-context workflows

Load the appropriate reference file based on the optimization need.
