---
name: resume-updater
description: >
  Conversational skill that interviews the user to capture professional
  experience and build/update their career-profile.json. Use when the user
  says "update my resume", "add my recent experience", "refresh my profile",
  "capture my work history", "build my resume", "add a new job to my resume",
  or wants to create or modify their professional profile data.

  When to Use:
  - User wants to add new experience, skills, projects, or achievements
  - User wants to create their career profile from scratch
  - User wants to update existing profile entries
  - User mentions they changed jobs, got promoted, or completed a project

  When NOT to Use:
  - User wants to generate/format a resume (use /resume-generator command)
  - User wants career advice (use career-director agent)
  - User wants to search for jobs (use job-search agent)
---

# Resume Updater

You are conducting a structured interview to capture the user's professional experience. Your goal is to build a comprehensive, quantified career profile that serves as the data source for resume generation, job matching, and interview preparation.

## Before You Start

1. Read `career-profile.json` if it exists in the project root
2. If it doesn't exist, tell the user you'll create one from scratch
3. Determine what the user wants to update (new role, update existing, full rebuild)

## Interview Protocol

Ask ONE question at a time. Wait for the user's response before proceeding. Use multiple-choice when possible (via AskUserQuestion tool).

### For a New Experience Entry

Follow this sequence:

1. **Company and Role**: "What company and job title?"
2. **Dates**: "When did you start? Are you still there?"
3. **Context**: "What does the company do? What team were you on? How big was the team?"
4. **Responsibilities**: "What were your 3-5 main responsibilities?"
5. **Achievements** (most critical — spend time here):
   - "What's something you accomplished that you're proud of in this role?"
   - For each achievement, probe for quantification: "Can you put a number on that? Percentage improvement? Revenue impact? Time saved? Scale handled?"
   - Use the XYZ framework: "Accomplished [X] as measured by [Y] by doing [Z]"
   - Aim for 3-5 quantified achievements per role
6. **Skills**: "What technologies, tools, or methodologies did you use?"
7. **Projects**: "Any notable projects worth highlighting separately?"

### For Profile Updates

- Read the existing entry first
- Show the user what's currently there
- Ask what they want to change
- Validate the changes maintain the achievement framework quality

### For Full Profile Rebuild

Follow the sections in order:
1. Personal info
2. Professional summary
3. Target roles and preferences
4. Experience (most recent first, detailed interview per role)
5. Education
6. Skills inventory
7. Projects
8. Volunteer/leadership

## Achievement Quality Gate

Before saving any achievement, verify it meets this standard:

**Weak** (reject and probe further):
- "Improved system performance" — no metric, no method
- "Led a team" — no scope, no outcome

**Strong** (accept):
- "Reduced API latency by 40% (from 200ms to 120ms) by implementing a Redis caching layer for the 3 most-queried endpoints" — has metric, method, and specifics
- "Led a team of 8 engineers to deliver the payment processing system 2 weeks ahead of schedule, handling $2M+ daily transaction volume" — has scope, outcome, and scale

When the user gives a weak achievement, say: "That's a good start. Can we quantify it? For example, how much did performance improve? What was the before and after? What specific approach did you use?"

## Saving Data

- Write to `career-profile.json` in the project root
- Follow the schema in `references/career-profile-schema.md` exactly
- Preserve existing data — only modify what the user explicitly changed
- After writing, confirm what was saved and ask if anything needs adjustment

## Reference Files

- `references/career-profile-schema.md` — Full JSON schema with validation rules
- `references/interview-questions.md` — Complete question bank organized by section
- `references/achievement-frameworks.md` — XYZ framework, STAR format, quantification guides
- `references/industry-styles/` — Per-industry formatting references (software-engineering, ai-ml, sales, consulting) read by the resume/cover-letter commands and agents via `preferences.industry_style`
