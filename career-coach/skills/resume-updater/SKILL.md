---
name: resume-updater
description: Builds and maintains the user's career profile (career-profile.json), the record of experience, achievements, skills and job targets that every career-coach command reads. Use when the user wants to set up their career profile, pastes or points to an existing resume or LinkedIn text to import, adds a new job, promotion or project, or wants to strengthen achievements with numbers. Not for producing a formatted resume or cover letter (use /resume-generator or /cover-letter), checking a resume against a job posting (/ats-check), or career strategy (career-director agent).
---

# Resume updater

Build and keep current the user's `career-profile.json`: an accurate, quantified record of their career that resumes, cover letters, job matching and interview prep all draw on. The quality of everything downstream depends on two things here: the facts are the user's own, and achievements carry real numbers wherever the user can supply them.

Read `references/working-files.md` for where files live and the honesty rule that applies to everything you write.

## Start from what the user already has

Check for `career-profile.json` in the project root.

- **No profile yet:** ask first whether they have a resume, LinkedIn "About/Experience" text, or a file you can read (PDF, DOCX converted to text, Markdown). Importing takes a minute; building from scratch takes a long interview.
  - **If they paste or point to one:** parse it into the schema in `references/career-profile-schema.md`. Show a short summary of what you captured (roles, dates, how many achievements have numbers), write the file, and then ask only about the gaps that matter most: target roles and locations, achievements without numbers, and anything ambiguous like overlapping dates.
  - **If they have nothing to import:** run the intake in `references/profile-intake-questions.md`. Ask about one topic at a time so they can give full answers, but group simple fields (name, email, location, links) into one question.
- **Profile exists:** read it, show the user what's relevant to their request, and change only what they asked to change. Preserve everything else exactly.

## Capturing a role

For each role, get company, title, dates (YYYY-MM), a line of context (what the company does, team and size), 3-5 responsibilities, the skills used, and the achievements. Achievements deserve the most time because they're what a reader remembers:

- Ask what they're proud of in the role, then probe for a number: percentage improvement, revenue, time saved, scale handled, before and after. The XYZ shape helps: "Accomplished X, as measured by Y, by doing Z" (`references/achievement-frameworks.md` has more prompts by role type).
- Probe once or twice. If no honest number exists (some real achievements don't have one), save the statement and method with an empty `metric`, tell the user it'll show up as a to-do, and move on. Never estimate a number for them; a made-up metric on a resume can cost them an offer when it's questioned in an interview.

What good looks like:

- Weak: "Improved system performance." No measure, no method.
- Strong: "Reduced API latency 40% (200ms to 120ms) by adding a Redis cache to the three most-queried endpoints."

## Targets and style

Make sure the profile has `target.roles` (at most 5), locations, remote preference, a salary range if they're willing to share it, and `preferences.industry_style`. Infer the style from their target roles and history, confirm it with the user (AskUserQuestion works well here), and save it; every resume and interview command uses it. Custom styles go in the project's `./industry-styles/` folder (see `references/working-files.md`).

Publications, patents and talks go in `publications`.

## Saving

Write `career-profile.json` in the project root following the schema exactly, and preserve existing data. Saving triggers an automatic check: the plugin's hook reports formatting problems and achievements still missing numbers. Fix formatting issues directly; treat missing numbers as questions for the user, never as something to fill in yourself. After saving, tell the user what changed and what the most useful next step is, for example `/resume-generator` or `/job-hunt`.

## Reference files

- `references/career-profile-schema.md`: the JSON schema and validation rules
- `references/profile-intake-questions.md`: questions by profile section, for building or filling gaps
- `references/achievement-frameworks.md`: XYZ and STAR, quantification prompts by role type
- `references/working-files.md`: file locations, the honesty rule, industry-style lookup, tracker schemas
- `references/industry-styles/`: per-industry formatting, tone, keywords and interview weighting
- `references/negotiation-guide.md`: used by `/compare-offers`
