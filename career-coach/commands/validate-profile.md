---
description: Validate career-profile.json against the schema and get a completeness scorecard with fixes
argument-hint: "[optional path to profile, defaults to career-profile.json]"
---
Validate the user's career profile and turn the findings into an action plan.

## Arguments

$ARGUMENTS

Optional path to the profile file; default is `career-profile.json` in the project root.

## Protocol

### 1. Run the validator

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate-profile.py" career-profile.json
```

(substitute the path from the arguments if one was given). The script is advisory — it always exits 0 and reports findings as a completeness scorecard plus `WARN` lines. It checks the rules from `${CLAUDE_PLUGIN_ROOT}/skills/resume-updater/references/career-profile-schema.md`:

- Required fields (`personal.name`, `personal.email`, at least one experience entry)
- Dates in `YYYY-MM` format (education graduation may be `YYYY`)
- Experience in reverse-chronological order
- Maximum 5 target roles
- Every achievement has a non-empty `metric` (listed per role when missing)

### 2. Interpret the results

Don't just paste the output. Summarize:

- The completeness score and what it means
- **Blocking issues** (missing required fields, malformed dates) — these break resume generation and job matching; fix them first
- **Quality issues** (achievements without metrics) — these are the difference between a responsibilities list and a resume; for each flagged achievement, show the current statement and ask the user the quantification question from the resume-updater skill ("Can you put a number on that? Percentage? Revenue? Time saved? Scale?")

### 3. Offer fixes

- For mechanical issues (date formats, ordering, trimming target roles), offer to fix `career-profile.json` directly with Edit — show the change before applying.
- For missing metrics or empty sections, offer to run the resume-updater skill's interview flow to fill them properly rather than inventing numbers. **Never fabricate metrics.**
- After any edits, re-run the validator to confirm the score improved. (Edits to `career-profile.json` also trigger the plugin's validation hook automatically, so warnings will resurface on save if anything regressed.)
