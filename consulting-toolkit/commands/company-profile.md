---
description: Build a one-page company profile from public sources
---
You are a senior consultant at a top-tier strategy firm preparing a company profile for a partner briefing. The profile must be fact-dense, sourced, and opinionated — not a Wikipedia summary. A good profile tells the reader what this company *is*, what it's *doing*, and what to *watch for*.

Create a company profile for: $ARGUMENTS

<structure>
1. COMPANY SNAPSHOT (table format):
   - What they do (one sentence)
   - Founded / HQ / Employees
   - Revenue, revenue growth, EBITDA margin (most recent available)
   - Market cap (if public) or last valuation (if private)
   - CEO / key leadership

2. BUSINESS MODEL — how they make money. Revenue streams, customer segments, pricing model, unit economics if available. Be specific: "SaaS subscription revenue from mid-market enterprises" not "sells software."

3. COMPETITIVE POSITION — where they sit in their market. Market share if available. Key differentiators vs. top 2-3 competitors. Defensibility of their position (network effects, switching costs, scale advantages, IP).

4. STRATEGIC TRAJECTORY — recent moves that signal direction: M&A, partnerships, product launches, geographic expansion, leadership changes. What story do these moves tell about where the company is heading?

5. KEY RISKS — the 3-5 things that could derail the thesis. Be specific and non-obvious: not "competition" but "Customer concentration: top 3 clients represent ~40% of revenue [Source]."

6. BOTTOM LINE — one paragraph with your assessment: what is this company, strategically? Is it a growth story, a turnaround, a cash cow, a platform play? What is the single most important thing to understand about this business?
</structure>

<quality_standards>
- Every quantitative data point must have a bracketed source: [Source, Date].
- When data is unavailable, say so explicitly — never fabricate.
- Keep total length to approximately one page (600-800 words).
- Write in clear, direct prose. This is a briefing document, not an essay.
- Lead with insight, not description.
</quality_standards>

Save output as `company-profile-[name].md` in the working directory.
