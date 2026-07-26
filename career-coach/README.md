# Career Coach — Claude Code Plugin

AI-powered career coaching, job search, and resume building plugin for Claude Code. Features a Career Director orchestrator, multi-platform job discovery via MCP, interview preparation, and LaTeX resume compilation.

## Prerequisites

- **Claude Code** CLI
- **Node.js** 18+ (for MCP server)
- **Optional:** LaTeX distribution (`texlive`, `mactex`) for PDF resume compilation
- **Optional:** Pandoc for Markdown-to-PDF conversion
- **Optional:** [Chrome MCP](https://github.com/anthropics/claude-code-chrome-mcp) for browser-based job application automation

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

2. **Select an output style** — Tell Claude your industry (software engineering, AI/ML, sales, consulting) to activate the matching resume format.

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
| `/resume-generator [job description or URL]` | Generate a tailored resume from your career profile, formatted for your active output style |
| `/cover-letter [job description or URL]` | Generate a targeted cover letter (250-400 words) with company research |

### Output Styles

Drop-in industry formatting that controls how resumes and career documents are structured:

| Style | Section Order |
|-------|--------------|
| **software-engineering** | Skills, Experience, Projects, Education |
| **ai-ml** | Experience, Publications/Research, Projects, Skills, Education |
| **sales** | Experience (revenue-first), Achievements, Skills, Education |
| **consulting** | Experience (client-impact), Education, Skills, Leadership |

**Add your own:** Create a `.md` file in `output-styles/` with frontmatter:

```yaml
---
name: your-style
description: When to activate this style
keep-coding-instructions: true
---
```

### MCP Server — Job Intelligence

5 tools for job market data:

| Tool | Sources | Description |
|------|---------|-------------|
| `job_search_jobs` | Indeed, LinkedIn, TrueUp | Aggregated job search with deduplication |
| `job_get_company_info` | Glassdoor | Company profiles, ratings, culture scores |
| `job_get_salary_data` | Glassdoor, Levels.fyi | Compensation comparison tables |
| `job_get_interview_experiences` | Glassdoor | Interview reports with difficulty ratings |
| `job_search_trending_roles` | TrueUp | Trending roles and market demand |

### Hooks

**LaTeX Auto-Compile** — PostToolUse hook that automatically compiles `.tex` or `.md` files written to `resumes/` into PDFs using xelatex or pandoc.

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

## Data Model

All components share a single `career-profile.json` file at the project root. See `skills/resume-updater/references/career-profile-schema.md` for the full schema.

### Chrome MCP Integration

For browser-based job application automation, install and configure [Chrome MCP](https://github.com/anthropics/claude-code-chrome-mcp) separately. The Career Director and Job Search agents are designed to use Chrome MCP tools when available for:
- Auto-filling job applications
- Saving job listings from browser
- LinkedIn profile data extraction

## License

MIT
