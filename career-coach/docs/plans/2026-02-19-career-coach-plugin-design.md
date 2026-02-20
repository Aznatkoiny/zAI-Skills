# Career Coach Plugin — Design Document

**Date:** 2026-02-19
**Plugin name:** `career-coach`
**Author:** Antony Zaki
**Pattern:** Modular Monolith (single plugin, shared career-profile.json contract)

---

## Overview

A Claude Code plugin for job search and career coaching. Supports four user personas: active job seekers, passive professionals, career changers, and those maintaining career readiness. Uses a hub-and-spoke agent architecture with a Career Director orchestrating specialist agents.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent coordination | Hub-and-spoke | Career Director routes to specialists, mirrors consulting-toolkit engagement-manager pattern |
| Career coach placement | Merged into Career Director | Director already holds full context; separate agent adds routing overhead without benefit |
| Data model | career-profile.json | Shared contract between all agents, skills, and commands. Single source of truth |
| MCP strategy | Hybrid: custom read-only + Chrome MCP | Ship read-only MCP for data; integrate Chrome MCP externally for automation |
| Output styles | Extensible framework | 4 starter styles; users add industries by dropping .md files |
| LaTeX hook | PostToolUse on Write | Auto-compiles resumes written to resumes/ directory |
| Resume data capture | Conversational skill | Interview-style data capture into career-profile.json |

## Directory Structure

```
career-coach/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json          (dev only)
├── agents/
│   ├── career-director.md        Hub orchestrator + career coaching
│   ├── job-search.md             Job discovery & application tracking
│   └── interview-prep.md         Interview coaching & mock interviews
├── skills/
│   └── resume-updater/
│       ├── SKILL.md              Interview-style data capture
│       └── references/
│           ├── interview-questions.md
│           ├── career-profile-schema.md
│           └── achievement-frameworks.md
├── commands/
│   ├── resume-generator.md       /resume-generator
│   └── cover-letter.md           /cover-letter
├── hooks/
│   ├── hooks.json
│   └── compile-latex.sh
├── output-styles/
│   ├── software-engineering.md
│   ├── ai-ml.md
│   ├── sales.md
│   └── consulting.md
├── mcp-servers/
│   └── job-intelligence/
│       ├── package.json
│       ├── tsconfig.json
│       └── src/
│           ├── index.ts
│           ├── tools/
│           │   ├── search-jobs.ts
│           │   ├── company-info.ts
│           │   ├── salary-data.ts
│           │   ├── interview-experiences.ts
│           │   └── trending-roles.ts
│           └── services/
│               ├── indeed.ts
│               ├── linkedin.ts
│               ├── trueup.ts
│               ├── glassdoor.ts
│               └── levelsfyi.ts
├── templates/
│   └── latex/
│       ├── modern-professional.tex
│       ├── technical-clean.tex
│       ├── jakes-resume.tex
│       ├── deedy-resume.tex
│       ├── altacv.tex
│       └── awesome-cv.tex
└── README.md
```

## Component Designs

### 1. Agents

#### Career Director (career-director.md)

- **Role:** Hub orchestrator + career coach
- **Model:** opus
- **Tools:** Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
- **Triggers:** Complex career requests, multi-step workflows, career advice, gap analysis, trajectory planning
- **Behaviors:**
  - Reads career-profile.json to understand user's current state
  - Routes to job-search or interview-prep based on intent
  - Spawns agent teams for complex workflows (e.g., career switch prep)
  - Maintains job-search-state.json for tracking active searches
  - Provides career coaching directly: gap analysis, trajectory planning, skill roadmaps
  - Industry-aware advice adapting to active output style

#### Job Search Agent (job-search.md)

- **Role:** Job discovery, matching, and application tracking
- **Model:** sonnet
- **Tools:** Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
- **Triggers:** "Find jobs", "search for roles", "what's available", job listings
- **Behaviors:**
  - Uses MCP tools to search LinkedIn, Indeed, TrueUp, Glassdoor
  - Matches jobs against career-profile.json skills and preferences
  - Tracks applications in applications.json (applied, interviewing, offer, rejected)
  - Scores job fit based on skill overlap, salary range, location preference
  - Can use Chrome MCP for automated applications when configured

#### Interview Prep Agent (interview-prep.md)

- **Role:** Interview coaching and mock interviews
- **Model:** sonnet
- **Tools:** Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
- **Triggers:** "Interview prep", "mock interview", "behavioral questions", "technical interview"
- **Behaviors:**
  - Pulls from career-profile.json to personalize STAR stories
  - Industry-specific question banks (technical, behavioral, case)
  - Mock interview simulation with feedback
  - Company-specific prep using MCP data (company info, Glassdoor reviews)
  - Tracks prep sessions and improvement areas

### 2. Resume Updater Skill

- **Trigger phrases:** "update my resume", "add experience", "capture my recent work", "refresh my profile"
- **Flow:**
  1. Read existing career-profile.json (or bootstrap new)
  2. Ask structured questions one at a time (role, company, achievements, skills)
  3. Use "accomplished X, as measured by Y, by doing Z" achievement framework
  4. Update career-profile.json with structured data
  5. Trigger resume re-generation
- **References:**
  - interview-questions.md — Question bank for conversational capture
  - career-profile-schema.md — Full schema with validation
  - achievement-frameworks.md — XYZ, STAR, quantification guides

### 3. career-profile.json Schema

```json
{
  "personal": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "github": "",
    "portfolio": ""
  },
  "summary": "",
  "target": {
    "roles": [],
    "industries": [],
    "locations": [],
    "salary_range": { "min": 0, "max": 0, "currency": "USD" },
    "remote_preference": "remote | hybrid | onsite | flexible"
  },
  "experience": [
    {
      "company": "",
      "title": "",
      "start_date": "",
      "end_date": "",
      "current": false,
      "responsibilities": [],
      "achievements": [
        {
          "statement": "",
          "metric": "",
          "method": ""
        }
      ],
      "skills_used": [],
      "projects": []
    }
  ],
  "education": [
    {
      "institution": "",
      "degree": "",
      "field": "",
      "graduation": "",
      "gpa": "",
      "honors": []
    }
  ],
  "skills": {
    "technical": [],
    "tools": [],
    "languages": [],
    "certifications": []
  },
  "projects": [
    {
      "name": "",
      "description": "",
      "url": "",
      "technologies": [],
      "impact": ""
    }
  ],
  "volunteer_leadership": [
    {
      "organization": "",
      "role": "",
      "start_date": "",
      "end_date": "",
      "description": "",
      "impact": ""
    }
  ],
  "preferences": {
    "industry_style": "software-engineering"
  }
}
```

### 4. Commands

#### /resume-generator

- Generates formatted resume from career-profile.json
- Accepts optional argument: target role/company for tailoring
- Uses active output style for formatting
- Writes to resumes/ directory (triggers LaTeX hook)

#### /cover-letter

- Generates tailored cover letter for a specific job posting
- Accepts argument: job URL or description
- Reads career-profile.json for experience matching
- Adapts tone based on active output style

### 5. LaTeX Hook

- **Event:** PostToolUse
- **Matcher:** Write tool, files in resumes/ directory
- **Script:** compile-latex.sh
  - Detects .md → converts to LaTeX via template, then compiles
  - Detects .tex → compiles directly with xelatex
  - Outputs PDF alongside source file
- **Templates:** 6 LaTeX templates (modern-professional, technical-clean, Jake's, Deedy, AltaCV, Awesome-CV)

### 6. Output Styles

4 starter styles, extensible via drop-in .md files:

| Style | Section Order | Metric Emphasis | Tone |
|-------|--------------|-----------------|------|
| software-engineering | Skills, Experience, Projects | Scale, latency, throughput | Direct, technical |
| ai-ml | Experience, Publications, Skills | Models, datasets, benchmarks | Academic-practitioner |
| sales | Experience, Achievements, Skills | Revenue, quota %, deal size | Action-oriented, results |
| consulting | Experience, Education, Skills | Client impact, methodologies | Structured, strategic |

Each style affects: resume formatting, cover letter tone, interview prep weighting, career advice framing.

### 7. MCP Server — Job Intelligence

TypeScript MCP server (matches consulting-toolkit financial-intelligence pattern).

**Tools:**

| Tool | Sources | Returns |
|------|---------|---------|
| search_jobs | Indeed, TrueUp, LinkedIn | Job listings: title, company, salary, location, description |
| get_company_info | Glassdoor, LinkedIn | Company overview, ratings, culture, interview process |
| get_salary_data | Glassdoor, Levels.fyi | Salary ranges by role, company, location |
| get_interview_experiences | Glassdoor | Interview questions, process, difficulty ratings |
| search_trending_roles | TrueUp | Hot roles, hiring velocity, market trends |

**Chrome MCP:** Integrated externally via .mcp.json config, documented in README. Not built as part of this plugin.

## File Count Estimate

- 3 agents
- 1 SKILL.md + 3 references
- 2 commands
- hooks.json + compile-latex.sh
- 4 output styles
- ~12 MCP source files
- 6 LaTeX templates
- plugin.json + README

**Total: ~35-40 files**

## Optimized Agent Prompts

Full prompt-optimized agent markdown files are included below. These follow Anthropic's Claude 4.x prompt optimization guidance: explicit behavioral specifications, XML-tagged sections for structured retrieval, bad/good example pairs, and state file contracts.

### Career Director Prompt

See `agents/career-director.md` — 175+ lines covering:
- Hub orchestration with structured delegation briefs
- Direct career coaching protocol (assess → analyze gaps → recommend path)
- Industry-aware advice adaptation
- State management via career-profile.json and job-search-state.json
- Quality gate on specialist agent output
- Communication style: lead with the answer, be direct, add coaching layer

Key prompt patterns applied:
- `<team>` tag for delegation context
- `<coaching_protocol>` with bad/good advice examples
- `<orchestration_protocol>` with brief template matching engagement-manager quality
- `<career_profile>` section explaining the data contract

### Job Search Agent Prompt

See `agents/job-search.md` — 120+ lines covering:
- MCP tool usage protocol (search_jobs, get_company_info, get_salary_data, etc.)
- Search protocol: load profile → execute multi-query search → score/rank → enrich
- Application tracking via applications.json with status workflow
- Output formatting: ranked tables with skill match scoring

Key prompt patterns applied:
- `<data_sources>` tag listing all MCP tools with usage guidance
- `<search_protocol>` with 4-step search workflow
- `<application_tracking>` with full JSON schema
- Parallel tool calling encouragement for data enrichment

### Interview Prep Agent Prompt

See `agents/interview-prep.md` — 140+ lines covering:
- Company-specific research protocol using MCP data
- Question bank organized by type (behavioral, technical, situational, culture)
- STAR story crafting from career-profile.json achievements
- Mock interview simulation with interviewer persona
- Feedback framework with bad/good feedback examples

Key prompt patterns applied:
- `<prep_protocol>` with 4-step preparation workflow
- `<feedback_framework>` with explicit bad/good feedback pair
- `<state_management>` with interview-prep-notes.json schema
- `<industry_adaptation>` for industry-specific prep strategies

## Open Questions

- LaTeX dependency: Should the hook gracefully degrade if pdflatex/xelatex isn't installed?
- Chrome MCP auth: How to handle LinkedIn/Indeed login sessions securely?
- Rate limiting: How to handle scraping rate limits across services?
