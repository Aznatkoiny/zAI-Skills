# Career Coach — Claude Code Plugin

AI-powered career coaching, job search, and resume building plugin for Claude Code. Features a Career Director orchestrator, multi-platform job discovery via MCP, interview preparation, and LaTeX resume compilation.

## Prerequisites

- **Claude Code** CLI
- **Node.js** 18+ (for MCP server)
- **Optional:** LaTeX distribution (`texlive`, `mactex`) for PDF resume compilation
- **Optional:** Pandoc for Markdown-to-PDF conversion
- **Optional:** The **Claude in Chrome** browser extension for browser-based job application automation (Anthropic's official extension — see the Claude in Chrome section of Anthropic's documentation for setup)

## Installation

```bash
# Add the marketplace
/plugin marketplace add Aznatkoiny/zAI-Skills

# Install the plugin
/plugin install career-coach@zAI-Skills
```

Then restart Claude Code.

The Job Intelligence MCP server ships as a prebuilt bundle (`mcp-servers/job-intelligence/dist/index.cjs`) and works immediately after install — no build step required.

To rebuild it from source (development only):

```bash
cd career-coach/mcp-servers/job-intelligence
npm install && npm run build
```

## Quick Start

1. **Build your career profile** — Run the resume updater skill by asking Claude to update your resume. It will interview you to capture your experience, achievements, and career goals into `career-profile.json`.

2. **Set your industry style** — Tell Claude your industry (software-engineering, ai-ml, sales, consulting). It's stored as `preferences.industry_style` in `career-profile.json` and selects the matching formatting reference for resumes, cover letters, coaching, and interview prep.

3. **Search for jobs** — Ask the Career Director to find jobs matching your profile. It delegates to the Job Search agent which queries Indeed, LinkedIn, TrueUp, Glassdoor, and Levels.fyi.

4. **Generate tailored resumes** — Use `/resume-generator` with a job description to produce a targeted resume.

5. **Prepare for interviews** — Ask for interview prep to activate the Interview Prep agent with mock interviews, behavioral question practice, and company-specific coaching.

## Components

### Agents

| Agent | Model | Description |
|-------|-------|-------------|
| **Career Director** | Opus | Hub orchestrator + career coach. Manages your career strategy, delegates to specialists, and provides coaching. |
| **Job Search** | Sonnet | Job discovery and application tracking. Searches multiple platforms, tracks applications, and monitors new listings. |
| **Interview Prep** | Sonnet | Mock interviews and coaching. Conducts practice sessions with real-time feedback and company-specific preparation. |

### Skill

**Resume Updater** — Interactive interview-style skill that captures your professional experience and builds your `career-profile.json`. Uses progressive questioning with achievement quality gates (every accomplishment needs a quantified metric).

### Commands

| Command | Description |
|---------|-------------|
| `/resume-generator [target] [--template <name>] [--output-dir <dir>]` | Generate a tailored resume from your career profile — Markdown by default, or rendered into one of the 6 LaTeX templates via `scripts/render-resume.py` |
| `/cover-letter [job description, URL, or company/role]` | Generate a targeted cover letter (250-400 words) with company research |
| `/job-hunt [role focus or 'from profile']` | Full pipeline: search jobs per target role, enrich the top ~10 with salary + company data, score by skill overlap, write ranked `job-search-results.md`, and seed `applications.json` |
| `/ats-check [job description text/URL] [resume file]` | ATS keyword coverage check of a resume + profile against a job description, with a concrete rewrite suggestion per missing keyword |
| `/mock-interview [company/role] [behavioral\|technical\|case]` | Mock interview with real reported questions, one at a time, with a session scorecard persisted to `interview-prep-notes.json` |
| `/compare-offers [offer details or 'interactive']` | Compare offers on benchmarked 4-year total comp (assumptions stated) with cost-of-living adjustment and negotiation talking points |
| `/validate-profile [path]` | Run `scripts/validate-profile.py` against `career-profile.json` and turn the completeness scorecard into fixes |
| `/follow-ups` | Flag tracker entries stale >14 days or with due next-actions, and draft follow-up emails in your industry tone |

### Industry Styles

Industry formatting references live in `skills/resume-updater/references/industry-styles/`. The commands and agents read the file matching `preferences.industry_style` in `career-profile.json`. Each file contains the full section order (with rationale), bullet writing rules with example bullets, an ATS keyword bank, tone/formatting rules, career ladder framing, and interview weighting for that industry:

| Style | Section Order |
|-------|--------------|
| **software-engineering** | Skills, Experience, Projects, Education |
| **ai-ml** | Experience, Publications/Research, Projects, Skills, Education |
| **sales** | Experience (revenue-first), Achievements, Skills, Education |
| **consulting** | Experience (client-impact), Education, Skills, Leadership |

**Add your own:** Create a `.md` file in `skills/resume-updater/references/industry-styles/` named after the style (e.g., `product-management.md`) covering section order, example bullets with metrics, ATS keywords, tone rules, and interview weighting — then set `preferences.industry_style` in `career-profile.json` to the file name (without `.md`).

### Negotiation Guide

`skills/resume-updater/references/negotiation-guide.md` is a practical offer-negotiation playbook: anchoring with market data, BATNA framing, a component-by-component flexibility table (base, equity, sign-on, level, review timing), ready-to-use scripts, and a get-it-in-writing checklist. `/compare-offers` grounds its negotiation talking points in this file; it's also readable on its own.

### MCP Server — Job Intelligence

5 tools for job market data:

| Tool | Sources | Description |
|------|---------|-------------|
| `job_search_jobs` | Indeed, LinkedIn, TrueUp | Aggregated job search with deduplication |
| `job_get_company_info` | Glassdoor | Company profiles, ratings, culture scores |
| `job_get_salary_data` | Glassdoor, Levels.fyi | Compensation comparison tables |
| `job_get_interview_experiences` | Glassdoor | Interview reports with difficulty ratings |
| `job_search_trending_roles` | TrueUp | Trending roles and market demand |

Tools surface to Claude Code as `mcp__job-intelligence__<tool_name>` (e.g., `mcp__job-intelligence__job_get_company_info`).

#### Optional job-source API keys

The server reads these environment variables when present. All are optional — without them, keyless sources (Remotive, RemoteOK, Greenhouse/Lever job boards) still work.

| Env var | Purpose |
|---------|---------|
| `ADZUNA_APP_ID` | Adzuna job-search API application ID |
| `ADZUNA_APP_KEY` | Adzuna job-search API application key |
| `USAJOBS_API_KEY` | USAJOBS (US federal jobs) API key |
| `USAJOBS_EMAIL` | Contact email USAJOBS requires in the request User-Agent |

### Hooks

Two PostToolUse hooks fire on `Write`/`Edit`/`MultiEdit` (both are non-blocking):

- **LaTeX Auto-Compile** (`hooks/compile-latex.sh`) — automatically compiles `.tex` or `.md` files written to `resumes/` into PDFs using xelatex or pandoc.
- **Profile Validation** (`hooks/validate-profile.sh`) — whenever `career-profile.json` is written or edited, runs `scripts/validate-profile.py` and feeds any `WARN` lines back to Claude as additional context, so schema and quality issues surface immediately after every save.

### Scripts

Plain-Python utilities in `scripts/` (stdlib only, Python 3.8+):

| Script | Purpose |
|--------|---------|
| `validate-profile.py [path]` | Advisory validator for `career-profile.json`: required fields, `YYYY-MM` dates, reverse-chronological experience, max 5 target roles, and a non-empty metric on every achievement. Prints a completeness scorecard + `WARN` lines; always exits 0. Used by `/validate-profile` and the validation hook. |
| `render-resume.py --template <name> [--profile p] [--output-dir d] [--templates-dir t]` | Merges `career-profile.json` into one of the six LaTeX templates: substitutes contact macros, generates experience/education/skills/project blocks with LaTeX escaping, writes `<output-dir>/<name>-<template>.tex`. Limitations (no proficiency levels, no per-experience locations, no one-page fitting) are documented in the script docstring. Used by `/resume-generator --template`. |

### LaTeX Templates

6 resume templates in `templates/latex/`:

| Template | Style |
|----------|-------|
| `modern-professional.tex` | Clean ATS-friendly single column |
| `technical-clean.tex` | Two-column with skill sidebar |
| `jakes-resume.tex` | Jake Gutierrez style, compact |
| `deedy-resume.tex` | Deedy two-column |
| `altacv.tex` | Colorful sidebar with photo |
| `awesome-cv.tex` | Elegant with icon header |

Render any template directly from your profile with `/resume-generator --template <name>` (e.g., `--template jakes-resume`); the generated `.tex` lands in `resumes/` and auto-compiles to PDF when a TeX Live installation with XeLaTeX is present.

## Data Model

All components share a single `career-profile.json` file at the project root. See `skills/resume-updater/references/career-profile-schema.md` for the full schema.

### Claude in Chrome Integration

For browser-based job application automation, install and enable Anthropic's official **Claude in Chrome** browser extension separately (see the Claude in Chrome section of Anthropic's documentation for setup and site permissions). When its browser tools are available, the Career Director and Job Search agents can use them for:
- Auto-filling job applications
- Saving job listings from the browser
- LinkedIn profile data extraction

## License

MIT
