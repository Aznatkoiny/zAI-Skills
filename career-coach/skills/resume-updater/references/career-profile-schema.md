# Career Profile Schema

The `career-profile.json` file is the single source of truth for the user's professional data. All agents, skills, and commands read from and write to this file.

## Location

Always stored at the project root as `career-profile.json`.

## Full Schema

```json
{
  "personal": {
    "name": "string — Full legal name",
    "email": "string — Primary contact email",
    "phone": "string — Phone with country code",
    "location": "string — City, State/Country",
    "linkedin": "string — Full LinkedIn URL",
    "github": "string — Full GitHub URL (optional)",
    "portfolio": "string — Portfolio/website URL (optional)"
  },
  "summary": "string — 2-3 sentence professional summary. Written in third person, emphasizing value proposition for target roles.",
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
    "industry_style": "string — Active industry style; selects the formatting reference in references/industry-styles/ ('software-engineering', 'ai-ml', 'sales', or 'consulting')"
  }
}
```

## Validation Rules

1. **Required fields**: `personal.name`, `personal.email`, at least one entry in `experience`
2. **Dates**: Always YYYY-MM format for consistency
3. **Achievements**: Every achievement SHOULD have all three fields (statement, metric, method). The `metric` field is the most important — without quantification, achievements are just responsibilities.
4. **Experience order**: Most recent first (reverse chronological)
5. **Skills**: No duplicates within a category. Skills should be specific (e.g., "PyTorch 2.x" not just "Python")
6. **Target roles**: Maximum 5 target roles to maintain focus

## Usage by Component

| Component | Reads | Writes |
|-----------|-------|--------|
| Career Director | Full profile | target, preferences |
| Job Search Agent | target, skills, experience | — |
| Interview Prep Agent | experience, achievements, skills, projects | — |
| Resume Updater Skill | Full profile | Full profile |
| /resume-generator | Full profile | — |
| /cover-letter | Full profile + target | — |
