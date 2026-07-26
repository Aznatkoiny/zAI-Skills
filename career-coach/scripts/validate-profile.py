#!/usr/bin/env python3
"""validate-profile.py — advisory validator for career-profile.json.

Checks the profile against the rules in
skills/resume-updater/references/career-profile-schema.md:

  1. Required fields: personal.name, personal.email, at least one experience entry
  2. Dates in YYYY-MM format (experience, volunteer_leadership; education
     graduation may be YYYY or YYYY-MM)
  3. Experience in reverse-chronological order (most recent start_date first)
  4. Maximum 5 target roles
  5. Every achievement has a non-empty `metric`

Output: a completeness scorecard plus one `WARN` line per finding (missing
metrics are listed per role). This validator is ADVISORY: it always exits 0
so it never blocks a write — consumers should read the WARN lines.

Usage:
    python3 validate-profile.py [path/to/career-profile.json]

Defaults to ./career-profile.json when no path is given.
"""

import json
import re
import sys

DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
YEAR_OR_DATE_RE = re.compile(r"^\d{4}(-(0[1-9]|1[0-2]))?$")

MAX_TARGET_ROLES = 5


def warn(warnings, message):
    warnings.append(message)


def check_date(warnings, value, label, allow_year_only=False):
    """Validate a date string; None/empty is the caller's concern."""
    if value is None or value == "":
        return
    if not isinstance(value, str):
        warn(warnings, f"{label}: date must be a string in YYYY-MM format, got {value!r}")
        return
    pattern = YEAR_OR_DATE_RE if allow_year_only else DATE_RE
    expected = "YYYY or YYYY-MM" if allow_year_only else "YYYY-MM"
    if not pattern.match(value):
        warn(warnings, f"{label}: date {value!r} is not in {expected} format")


def validate(profile):
    """Return (warnings, scorecard_lines)."""
    warnings = []
    score_have = 0
    score_total = 0
    scorecard = []

    def score(label, ok, detail=""):
        nonlocal score_have, score_total
        score_total += 1
        if ok:
            score_have += 1
        mark = "OK  " if ok else "MISS"
        suffix = f" — {detail}" if detail else ""
        scorecard.append(f"  [{mark}] {label}{suffix}")

    # --- 1. Required fields -------------------------------------------------
    personal = profile.get("personal") or {}
    name = (personal.get("name") or "").strip()
    email = (personal.get("email") or "").strip()
    experience = profile.get("experience") or []

    score("personal.name", bool(name))
    if not name:
        warn(warnings, "personal.name is required and is missing or empty")
    score("personal.email", bool(email))
    if not email:
        warn(warnings, "personal.email is required and is missing or empty")
    score("experience (at least one entry)", bool(experience),
          f"{len(experience)} entr{'y' if len(experience) == 1 else 'ies'}")
    if not experience:
        warn(warnings, "experience must contain at least one entry")

    # Optional-but-recommended sections, surfaced in the scorecard only.
    score("summary", bool((profile.get("summary") or "").strip()))
    score("target.roles", bool((profile.get("target") or {}).get("roles")))
    score("education", bool(profile.get("education")))
    score("skills.technical", bool((profile.get("skills") or {}).get("technical")))
    score("preferences.industry_style",
          bool((profile.get("preferences") or {}).get("industry_style")))

    # --- 2. Date formats ----------------------------------------------------
    for i, exp in enumerate(experience):
        if not isinstance(exp, dict):
            warn(warnings, f"experience[{i}] must be an object")
            continue
        who = f"experience[{i}] ({exp.get('company', '?')} — {exp.get('title', '?')})"
        start = exp.get("start_date")
        if not start:
            warn(warnings, f"{who}: start_date is missing")
        else:
            check_date(warnings, start, f"{who} start_date")
        end = exp.get("end_date")
        if end:  # null/empty means current role — allowed
            check_date(warnings, end, f"{who} end_date")
        elif not exp.get("current"):
            warn(warnings, f"{who}: end_date is empty but 'current' is not true")

    for i, edu in enumerate(profile.get("education") or []):
        if isinstance(edu, dict):
            check_date(warnings, edu.get("graduation"),
                       f"education[{i}] ({edu.get('institution', '?')}) graduation",
                       allow_year_only=True)

    for i, vol in enumerate(profile.get("volunteer_leadership") or []):
        if isinstance(vol, dict):
            who = f"volunteer_leadership[{i}] ({vol.get('organization', '?')})"
            check_date(warnings, vol.get("start_date"), f"{who} start_date")
            if vol.get("end_date"):
                check_date(warnings, vol.get("end_date"), f"{who} end_date")

    # --- 3. Reverse-chronological experience --------------------------------
    dated = [
        (i, exp.get("start_date"))
        for i, exp in enumerate(experience)
        if isinstance(exp, dict) and isinstance(exp.get("start_date"), str)
        and DATE_RE.match(exp.get("start_date"))
    ]
    for (i_a, d_a), (i_b, d_b) in zip(dated, dated[1:]):
        if d_a < d_b:  # YYYY-MM sorts lexicographically
            warn(warnings,
                 f"experience is not reverse-chronological: entry [{i_a}] "
                 f"(start {d_a}) appears before entry [{i_b}] (start {d_b})")
    in_order = not any(d_a < d_b for (_, d_a), (_, d_b) in zip(dated, dated[1:]))
    score("experience reverse-chronological", bool(experience) and in_order)

    # --- 4. Max 5 target roles ----------------------------------------------
    roles = (profile.get("target") or {}).get("roles") or []
    if len(roles) > MAX_TARGET_ROLES:
        warn(warnings,
             f"target.roles has {len(roles)} entries; maximum is {MAX_TARGET_ROLES} "
             "to maintain focus")
    score(f"target.roles <= {MAX_TARGET_ROLES}", len(roles) <= MAX_TARGET_ROLES,
          f"{len(roles)} role(s)")

    # --- 5. Achievement metrics (listed per role) ---------------------------
    total_ach = 0
    ach_with_metric = 0
    for i, exp in enumerate(experience):
        if not isinstance(exp, dict):
            continue
        who = f"experience[{i}] ({exp.get('company', '?')} — {exp.get('title', '?')})"
        achievements = exp.get("achievements") or []
        if not achievements:
            warn(warnings, f"{who}: no achievements — aim for 3-5 quantified achievements")
            continue
        missing = []
        for j, ach in enumerate(achievements):
            total_ach += 1
            metric = ""
            if isinstance(ach, dict):
                metric = (ach.get("metric") or "").strip()
                statement = (ach.get("statement") or "").strip()
            else:
                statement = str(ach)
            if metric:
                ach_with_metric += 1
            else:
                label = statement[:60] + ("..." if len(statement) > 60 else "")
                missing.append((j, label or "<no statement>"))
        for j, label in missing:
            warn(warnings, f"{who}: achievement [{j}] has no metric — \"{label}\"")
    score("all achievements have metrics",
          total_ach > 0 and ach_with_metric == total_ach,
          f"{ach_with_metric}/{total_ach} quantified")

    return warnings, scorecard, score_have, score_total


def main(argv):
    path = argv[1] if len(argv) > 1 else "career-profile.json"

    try:
        with open(path, "r", encoding="utf-8") as fh:
            profile = json.load(fh)
    except FileNotFoundError:
        print(f"WARN {path} not found — run the resume-updater skill to create it")
        return 0
    except json.JSONDecodeError as exc:
        print(f"WARN {path} is not valid JSON: {exc}")
        return 0

    if not isinstance(profile, dict):
        print(f"WARN {path} must contain a JSON object at the top level")
        return 0

    warnings, scorecard, have, total = validate(profile)

    pct = round(100 * have / total) if total else 0
    print(f"Career profile completeness: {have}/{total} checks passed ({pct}%)")
    print("Scorecard:")
    for line in scorecard:
        print(line)
    print()

    if warnings:
        print(f"{len(warnings)} warning(s):")
        for w in warnings:
            print(f"WARN {w}")
    else:
        print("No warnings — profile looks complete.")

    # Advisory tool: never block the caller.
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
