# Career Profile Schema

The `career-profile.json` file is the single source of truth for the user's professional data. All agents, skills, and commands read from and write to this file.

## Location

Always stored at the project root as `career-profile.json`.

## Full Schema

```json
{
  "personal": {
    "name": "string — Name as the user wants it on their resume",
    "email": "string — Primary contact email",
    "phone": "string — Phone with country code",
    "location": "string — City, State/Country",
    "linkedin": "string — Full LinkedIn URL",
    "github": "string — Full GitHub URL (optional)",
    "portfolio": "string — Portfolio/website URL (optional)"
  },
  "summary": "string — 2-3 sentence professional summary in implied first person (no 'I', no pronouns), emphasizing value for the target roles.",
  "target": {
    "roles": ["string — Target job titles, e.g., 'Senior ML Engineer', 'Staff Software Engineer'"],
    "industries": ["string — Target industries, e.g., 'AI/ML', 'FinTech', 'Healthcare'"],
    "locations": ["string — Preferred locations, e.g., 'San Francisco, CA', 'Remote'"],
    "salary_range": {
      "min": "number — Minimum acceptable base salary in USD",
      "max": "number — Target/ideal base salary in USD",
      "currency": "string — ISO 4217 code, default 'USD'"
    },
    "remote_preference": "string — One of: 'remote', 'hybrid', 'onsite', 'flexible'"
  },
  "experience": [
    {
      "company": "string — Company name",
      "title": "string — Job title",
      "start_date": "string — YYYY-MM format",
      "end_date": "string — YYYY-MM format or null if current",
      "current": "boolean — true if this is the current role",
      "responsibilities": ["string — Key responsibility descriptions"],
      "achievements": [
        {
          "statement": "string — Full achievement statement",
          "metric": "string — Quantified result (e.g., '40% reduction in latency')",
          "method": "string — How it was accomplished (e.g., 'by implementing Redis caching layer')"
        }
      ],
      "skills_used": ["string — Technologies and skills used in this role"],
      "projects": ["string — Notable project names or descriptions"]
    }
  ],
  "education": [
    {
      "institution": "string — University/school name",
      "degree": "string — Degree type (e.g., 'B.S.', 'M.S.', 'Ph.D.')",
      "field": "string — Field of study",
      "graduation": "string — YYYY or YYYY-MM format",
      "gpa": "string — GPA if notable (3.5+), otherwise omit",
      "honors": ["string — Dean's list, cum laude, etc."]
    }
  ],
  "skills": {
    "technical": ["string — Programming languages, frameworks, algorithms"],
    "tools": ["string — Software tools, platforms, IDEs"],
    "languages": ["string — Spoken languages with proficiency"],
    "certifications": ["string — Professional certifications with dates"]
  },
  "projects": [
    {
      "name": "string — Project name",
      "description": "string — 1-2 sentence description",
      "url": "string — GitHub/demo URL (optional)",
      "technologies": ["string — Tech stack used"],
      "impact": "string — Quantified impact or outcome"
    }
  ],
  "publications": [
    {
      "title": "string — Paper, patent, talk, or article title",
      "venue": "string — Journal, conference, patent office, or event",
      "year": "string — YYYY",
      "url": "string — Link (optional)",
      "type": "string — One of: 'paper', 'patent', 'talk', 'article' (optional)"
    }
  ],
  "volunteer_leadership": [
    {
      "organization": "string — Organization name",
      "role": "string — Role/title",
      "start_date": "string — YYYY-MM format",
      "end_date": "string — YYYY-MM format or null if current",
      "description": "string — What you did",
      "impact": "string — Quantified impact or outcome"
    }
  ],
  "preferences": {
    "industry_style": "string — Active industry style; selects the formatting reference (bundled: 'software-engineering', 'ai-ml', 'sales', 'consulting'; a custom style is any name with a file in the project's ./industry-styles/ folder)"
  }
}
```

## Validation Rules

1. **Required fields**: `personal.name`, `personal.email`, at least one entry in `experience`
2. **Dates**: YYYY-MM for experience and volunteer entries; education graduation may be YYYY
3. **Achievements**: Aim for all three fields (statement, metric, method). A metric is what turns a responsibility into an achievement, so it's worth probing for one; but when no honest number exists, save the achievement with an empty `metric` rather than an estimate. The validator flags these as to-dos.
4. **Experience order**: Most recent first (reverse chronological)
5. **Skills**: No duplicates within a category. Skills should be specific (e.g., "PyTorch 2.x" not just "Python")
6. **Target roles**: Maximum 5 target roles to maintain focus

## Usage by Component

| Component | Reads | Writes |
|-----------|-------|--------|
| resume-updater skill | Full profile | Full profile |
| career-director agent | Full profile | — (suggests changes; the skill writes them) |
| job-search agent, /job-hunt | target, skills, experience | — |
| interview-prep agent, /mock-interview | experience, achievements, skills, projects | — |
| /resume-generator, /cover-letter, /ats-check | Full profile | — |
| /compare-offers, /follow-ups | target, preferences | — |
| /validate-profile | Full profile | Mechanical fixes only, with the user's OK |
