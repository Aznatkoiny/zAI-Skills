---
description: Flag stale applications and due next-actions from the tracker and draft follow-up emails
argument-hint: "[none — reads applications.json]"
---
Review the user's application tracker for anything that needs a nudge, and draft the follow-up emails.

## Arguments

$ARGUMENTS

This command takes no required arguments — it reads `applications.json` from the project root. If arguments name a specific company, limit the review to that company's entries.

If `applications.json` doesn't exist or has no applications, say so and suggest `/job-hunt` to start populating it.

## Protocol

### 1. Find entries needing attention

Read `applications.json` and today's date. Flag entries where:

- **Stale**: `last_updated` (or `date_applied` when `last_updated` is empty) is more than **14 days ago** AND the status is still active (`applied`, `phone_screen`, `technical`, `onsite` — not `saved`, `offer`, `rejected`, or `withdrawn`)
- **Due**: `next_action_date` is today or in the past, whatever the status

For `saved` entries older than 14 days, don't draft a follow-up — list them separately as "decide: apply or drop".

### 2. Report

Show a table:

| Company | Role | Status | Days since update | Next action | Why flagged |
|---------|------|--------|-------------------|-------------|-------------|

### 3. Draft follow-up emails

For each flagged active entry, draft a short follow-up email. Match the tone rules of the user's industry style — read `preferences.industry_style` from `career-profile.json` and the corresponding file at `${CLAUDE_PLUGIN_ROOT}/skills/resume-updater/references/industry-styles/<industry_style>.md`, applying the same tone and no-generic-phrases rules the `/cover-letter` command uses.

Email rules:
- 60-120 words; subject line included
- Reference the specific stage ("since our phone screen on…", "since I applied on…") using dates and contacts from the tracker entry
- Add one line of genuine value where the profile supports it (a relevant recent accomplishment, a link to work) — never invented
- Warm, direct close with a clear ask (status check or next step); zero desperation, no guilt-tripping
- Address a named contact from `contacts` when one exists, otherwise the recruiting team

Present the drafts in the chat for the user to copy — do not send anything.

### 4. Update the tracker

After the user reviews the drafts, offer to update `applications.json`: set `next_action` (e.g., "await reply to follow-up sent YYYY-MM-DD"), set `next_action_date` about a week out, refresh `last_updated`, append a note, and keep the `summary` section's counts current. Only update entries the user actually acted on.
