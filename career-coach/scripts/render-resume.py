#!/usr/bin/env python3
"""render-resume.py — merge career-profile.json into a LaTeX resume template.

Reads a template from templates/latex/, substitutes its contact
``\\newcommand`` macros with profile data, regenerates the document body
(between ``\\begin{document}`` and ``\\end{document}``) using the template's
own macros and section styling, and writes ``<output-dir>/<name>-<template>.tex``.
All profile text is escaped for LaTeX (&, %, $, #, _, {, }, ~, ^, \\).

Usage:
    python3 render-resume.py --template jakes-resume \\
        [--profile career-profile.json] [--output-dir resumes] \\
        [--templates-dir /path/to/templates/latex]

Templates: jakes-resume | deedy-resume | altacv | awesome-cv |
           modern-professional | technical-clean

KNOWN LIMITATIONS (honest list):
  * The body is regenerated from the profile, so hand-edits inside a
    template's ``\\begin{document}...\\end{document}`` block are not carried
    over; the preamble (fonts, colors, macros) is preserved as-is.
  * The career-profile schema has no per-skill proficiency levels, so
    technical-clean skill bars default to 0.85 and altacv dot ratings
    default to 4/5. Edit the generated .tex to adjust.
  * The schema has no per-experience location field. If an experience entry
    happens to include a "location" key it is used; otherwise the location
    slot is left empty.
  * No one-page fitting: long profiles can overflow a page. Trim bullets in
    the profile or the generated .tex.
  * Publications/Recognition/Coursework sections present in some template
    examples are omitted — the profile schema has no fields for them.
  * altacv's photo stays a placeholder circle (no photo field in the schema).
  * Templates require XeLaTeX with TeX Gyre fonts (TeX Live); awesome-cv
    additionally needs fontawesome5.
  * Escaping is plain-text only: profile values containing intentional LaTeX
    markup will be escaped literally, not interpreted.
"""

import argparse
import json
import re
import sys
from pathlib import Path

TEMPLATES = (
    "jakes-resume",
    "deedy-resume",
    "altacv",
    "awesome-cv",
    "modern-professional",
    "technical-clean",
)

# ---------------------------------------------------------------------------
# LaTeX escaping
# ---------------------------------------------------------------------------

_LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_LATEX_RE = re.compile("|".join(re.escape(c) for c in _LATEX_SPECIALS))


def esc(value):
    """Escape LaTeX special characters in a plain-text value."""
    if value is None:
        return ""
    return _LATEX_RE.sub(lambda m: _LATEX_SPECIALS[m.group()], str(value))


def esc_join(items, sep=", "):
    return sep.join(esc(i) for i in items if i)


# ---------------------------------------------------------------------------
# Profile helpers
# ---------------------------------------------------------------------------

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def fmt_date(value):
    """YYYY-MM -> 'Jan 2022'; YYYY passes through; None/'' -> ''."""
    if not value:
        return ""
    m = re.match(r"^(\d{4})-(\d{2})$", str(value))
    if m:
        year, month = m.group(1), int(m.group(2))
        if 1 <= month <= 12:
            return f"{_MONTHS[month - 1]} {year}"
    return str(value)


def date_range(entry):
    start = fmt_date(entry.get("start_date"))
    end = "Present" if entry.get("current") or not entry.get("end_date") \
        else fmt_date(entry.get("end_date"))
    if start and end:
        return f"{start} -- {end}"
    return start or end


def strip_url(url):
    """Drop scheme + trailing slash: templates prepend https:// themselves."""
    if not url:
        return ""
    return re.sub(r"^https?://", "", str(url)).rstrip("/")


def exp_bullets(exp, cap=5):
    """Achievements first (they carry metrics), then responsibilities."""
    bullets = []
    for ach in exp.get("achievements") or []:
        if isinstance(ach, dict):
            text = (ach.get("statement") or "").strip()
            if not text:
                parts = [p for p in (ach.get("metric"), ach.get("method")) if p]
                text = " ".join(str(p).strip() for p in parts)
        else:
            text = str(ach).strip()
        if text:
            bullets.append(text)
    for resp in exp.get("responsibilities") or []:
        if len(bullets) >= cap:
            break
        if resp and str(resp).strip():
            bullets.append(str(resp).strip())
    return bullets[:cap]


def degree_line(edu):
    degree = (edu.get("degree") or "").strip()
    field = (edu.get("field") or "").strip()
    if degree and field:
        return f"{degree} {field}"
    return degree or field


def headline(profile):
    """A role headline: first target role, else most recent job title."""
    roles = (profile.get("target") or {}).get("roles") or []
    if roles:
        return roles[0]
    experience = profile.get("experience") or []
    if experience and isinstance(experience[0], dict):
        return experience[0].get("title") or ""
    return ""


def split_name(name):
    parts = (name or "").strip().split()
    if len(parts) >= 2:
        return " ".join(parts[:-1]), parts[-1]
    return name or "", ""


# ---------------------------------------------------------------------------
# Preamble macro substitution
# ---------------------------------------------------------------------------

def set_macro(preamble, macro, value):
    """Replace the value of \\newcommand{\\macro}{...} (single-level braces)."""
    pattern = re.compile(
        r"(\\newcommand\{\\" + re.escape(macro) + r"\}\{)[^{}]*(\})")
    return pattern.sub(lambda m: m.group(1) + value + m.group(2), preamble)


def fill_contact_macros(preamble, profile):
    p = profile.get("personal") or {}
    first, last = split_name(p.get("name"))
    values = {
        "resumeName": esc(p.get("name")),
        "resumeFirstName": esc(first),
        "resumeLastName": esc(last),
        "resumeSubtitle": esc(headline(profile)),
        "resumeTitle": esc(headline(profile)),
        "resumePhone": esc(p.get("phone")),
        "resumeEmail": esc(p.get("email")),
        "resumeLocation": esc(p.get("location")),
        "resumeLinkedIn": esc(strip_url(p.get("linkedin"))),
        "resumeGitHub": esc(strip_url(p.get("github"))),
        "resumeWebsite": esc(strip_url(p.get("portfolio"))),
    }
    for macro, value in values.items():
        preamble = set_macro(preamble, macro, value)
    return preamble


# ---------------------------------------------------------------------------
# Shared body fragments
# ---------------------------------------------------------------------------

def itemize(bullets, opts, item_cmd=None):
    if not bullets:
        return ""
    lines = [f"\\begin{{itemize}}[{opts}]"]
    for b in bullets:
        if item_cmd:
            lines.append(f"  {item_cmd}{{{esc(b)}}}")
        else:
            lines.append(f"  \\item {esc(b)}")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Per-template body builders
# Each returns the text that goes between \begin{document} and \end{document},
# using ONLY macros defined in that template's preamble.
# ---------------------------------------------------------------------------

def body_jakes(profile):
    p = profile.get("personal") or {}
    contact = ["\\resumePhone",
               "\\href{mailto:\\resumeEmail}{\\underline{\\resumeEmail}}"]
    if p.get("linkedin"):
        contact.append("\\href{https://\\resumeLinkedIn}{\\underline{\\resumeLinkedIn}}")
    if p.get("github"):
        contact.append("\\href{https://\\resumeGitHub}{\\underline{\\resumeGitHub}}")
    out = [
        "% ---- Header -------------------------------------------------",
        "\\begin{center}",
        "  {\\Huge\\scshape\\resumeName}\\\\[4pt]",
        "  \\small",
        "  " + "\\ $|$\\\n  ".join(contact),
        "\\end{center}",
        "",
    ]

    education = profile.get("education") or []
    if education:
        out += ["\\section{Education}", "\\resumeSubHeadingListStart"]
        for edu in education:
            honors = esc_join(edu.get("honors") or [])
            out += [
                "  \\resumeSubheading",
                f"    {{{esc(edu.get('institution'))}}}{{{honors}}}",
                f"    {{{esc(degree_line(edu))}}}{{{esc(fmt_date(edu.get('graduation')))}}}",
            ]
        out += ["\\resumeSubHeadingListEnd", ""]

    experience = profile.get("experience") or []
    if experience:
        out += ["\\section{Experience}", "\\resumeSubHeadingListStart", ""]
        for exp in experience:
            out += [
                "  \\resumeSubheading",
                f"    {{{esc(exp.get('title'))}}}{{{esc(date_range(exp))}}}",
                f"    {{{esc(exp.get('company'))}}}{{{esc(exp.get('location', ''))}}}",
            ]
            bullets = exp_bullets(exp)
            if bullets:
                out.append("    \\resumeItemListStart")
                for b in bullets:
                    out.append(f"      \\resumeItem{{{esc(b)}}}")
                out.append("    \\resumeItemListEnd")
            out.append("")
        out += ["\\resumeSubHeadingListEnd", ""]

    projects = profile.get("projects") or []
    if projects:
        out += ["\\section{Projects}", "\\resumeSubHeadingListStart", ""]
        for proj in projects:
            tech = esc_join(proj.get("technologies") or [])
            title = f"\\textbf{{{esc(proj.get('name'))}}}"
            if tech:
                title += f" $|$ \\emph{{{tech}}}"
            out.append(f"  \\resumeProjectHeading\n    {{{title}}}{{}}")
            bullets = [b for b in (proj.get("description"), proj.get("impact")) if b]
            if bullets:
                out.append("    \\resumeItemListStart")
                for b in bullets:
                    out.append(f"      \\resumeItem{{{esc(b)}}}")
                out.append("    \\resumeItemListEnd")
            out.append("")
        out += ["\\resumeSubHeadingListEnd", ""]

    skills = profile.get("skills") or {}
    rows = [("Technical", skills.get("technical")),
            ("Tools", skills.get("tools")),
            ("Certifications", skills.get("certifications")),
            ("Languages", skills.get("languages"))]
    rows = [(label, vals) for label, vals in rows if vals]
    if rows:
        out += [
            "\\section{Technical Skills}",
            "\\begin{itemize}[leftmargin=0.15in, label={}]",
            "  \\small{\\item{",
        ]
        for k, (label, vals) in enumerate(rows):
            tail = " \\\\" if k < len(rows) - 1 else ""
            out.append(f"    \\textbf{{{label}}}{{: {esc_join(vals)}}}{tail}")
        out += ["  }}", "\\end{itemize}", ""]

    return "\n".join(out)


def body_modern(profile):
    p = profile.get("personal") or {}
    line1 = ["\\resumeLocation" if p.get("location") else "",
             "\\href{tel:\\resumePhone}{\\resumePhone}" if p.get("phone") else "",
             "\\href{mailto:\\resumeEmail}{\\resumeEmail}"]
    line1 = [s for s in line1 if s]
    line2 = []
    if p.get("linkedin"):
        line2.append("\\href{https://\\resumeLinkedIn}{\\resumeLinkedIn}")
    if p.get("github"):
        line2.append("\\href{https://\\resumeGitHub}{\\resumeGitHub}")
    out = [
        "% ---- Header -------------------------------------------------",
        "\\begin{center}",
        "  {\\LARGE\\bfseries\\resumeName}\\\\[4pt]",
        "  \\small",
        "  " + "\\contactSep\n  ".join(line1) + ("\\\\" if line2 else ""),
    ]
    if line2:
        out.append("  " + "\\contactSep\n  ".join(line2))
    out += ["\\end{center}", ""]

    if profile.get("summary"):
        out += ["\\section{Summary}", esc(profile["summary"]), ""]

    experience = profile.get("experience") or []
    if experience:
        out.append("\\section{Experience}\n")
        for exp in experience:
            loc = exp.get("location", "")
            dates = esc(date_range(exp))
            if loc:
                out.append(f"\\expEntry{{{esc(exp.get('title'))}}}"
                           f"{{{esc(exp.get('company'))}}}{{{esc(loc)}}}{{{dates}}}")
            else:
                # \expEntry hard-codes "Location | Dates"; without a location
                # we inline the same styling minus the stray pipe.
                out.append(f"\\textbf{{{esc(exp.get('title'))}}} \\hfill "
                           f"\\textit{{{dates}}}\\\\\n"
                           f"\\textit{{\\color{{muted}}{esc(exp.get('company'))}}}"
                           f"\n\\vspace{{2pt}}")
            bl = itemize(exp_bullets(exp), "leftmargin=1.5em, itemsep=1pt, topsep=2pt")
            if bl:
                out.append(bl)
            out.append("\\vspace{6pt}\n")

    education = profile.get("education") or []
    if education:
        out.append("\\section{Education}\n")
        for edu in education:
            grad = esc(fmt_date(edu.get("graduation")))
            out.append(f"\\textbf{{{esc(degree_line(edu))}}} \\hfill "
                       f"\\textit{{{grad}}}\\\\\n"
                       f"\\textit{{\\color{{muted}}{esc(edu.get('institution'))}}}"
                       f"\n\\vspace{{2pt}}")
            extras = []
            if edu.get("gpa"):
                extras.append(f"GPA: {esc(edu['gpa'])}")
            if edu.get("honors"):
                extras.append(esc_join(edu["honors"]))
            if extras:
                out.append(
                    "\\begin{itemize}[leftmargin=1.5em, itemsep=1pt, topsep=2pt]\n"
                    "  \\item " + " \\quad|\\quad ".join(extras) + "\n"
                    "\\end{itemize}")
            out.append("\\vspace{4pt}\n")

    skills = profile.get("skills") or {}
    rows = [("Technical", skills.get("technical")),
            ("Tools", skills.get("tools")),
            ("Languages", skills.get("languages")),
            ("Certifications", skills.get("certifications"))]
    rows = [(label, vals) for label, vals in rows if vals]
    if rows:
        out += ["\\section{Skills}", "", "\\begin{tabular}{@{}l l}"]
        for label, vals in rows:
            out.append(f"  \\textbf{{{label}}} & {esc_join(vals)} \\\\")
        out += ["\\end{tabular}", ""]

    projects = profile.get("projects") or []
    if projects:
        out.append("\\section{Projects}\n")
        for proj in projects:
            url = esc(strip_url(proj.get("url")))
            head = f"\\textbf{{{esc(proj.get('name'))}}}"
            if url:
                head += f" \\hfill \\textit{{{url}}}"
            out.append(head + "\\\\")
            bullets = [b for b in (proj.get("description"), proj.get("impact")) if b]
            bl = itemize(bullets, "leftmargin=1.5em, itemsep=1pt, topsep=2pt")
            if bl:
                out.append(bl)
            out.append("\\vspace{4pt}\n")

    return "\n".join(out)


def _sidebar_contact_items(p, linkedin_macro=True, website=False):
    items = []
    if p.get("location"):
        items.append("      \\item {\\small \\resumeLocation}")
    if p.get("phone"):
        items.append("      \\item {\\small \\href{tel:\\resumePhone}{\\resumePhone}}")
    items.append("      \\item {\\small \\href{mailto:\\resumeEmail}{\\resumeEmail}}")
    if linkedin_macro and p.get("linkedin"):
        items.append("      \\item {\\small \\href{https://\\resumeLinkedIn}{\\resumeLinkedIn}}")
    if website and p.get("portfolio"):
        items.append("      \\item {\\small \\href{https://\\resumeWebsite}{\\resumeWebsite}}")
    return items


def body_technical_clean(profile):
    p = profile.get("personal") or {}
    skills = profile.get("skills") or {}
    out = [
        "\\noindent",
        "% ---- Two-column layout via minipage -------------------------",
        "\\begin{minipage}[t][\\paperheight][t]{\\sidebarW}",
        "  \\begin{tikzpicture}[remember picture, overlay]",
        "    \\fill[sidebarBg] (0,0) rectangle (\\sidebarW, -\\paperheight);",
        "  \\end{tikzpicture}",
        "  \\color{sidebarText}",
        "  \\hspace*{\\innerPad}\\begin{minipage}{\\sidebarW - 2\\innerPad}",
        "    \\vspace{\\innerPad}",
        "",
        "    {\\large\\bfseries\\color{white}\\resumeName}\\\\[2pt]",
        "    {\\small\\color{sidebarAccent}\\resumeTitle}",
        "",
        "    \\sideSection{Contact}",
        "    \\begin{itemize}[leftmargin=0pt, label={}, itemsep=2pt]",
    ]
    out += _sidebar_contact_items(p)
    if p.get("github"):
        out.append("      \\item {\\small \\href{https://\\resumeGitHub}{\\resumeGitHub}}")
    out += ["    \\end{itemize}", ""]

    technical = (skills.get("technical") or [])[:8]
    if technical:
        out += ["    \\sideSection{Technical Skills}",
                "    % NOTE: profile has no proficiency data; bars default to 0.85"]
        for s in technical:
            out.append(f"    \\skillbar{{{esc(s)}}}{{0.85}}")
        out.append("")

    education = profile.get("education") or []
    if education:
        out.append("    \\sideSection{Education}")
        for edu in education:
            out += [
                f"    {{\\small\\bfseries\\color{{white}}{esc(degree_line(edu))}}}\\\\",
                f"    {{\\small {esc(edu.get('institution'))}}}\\\\",
                f"    {{\\small\\color{{sidebarAccent}}{esc(fmt_date(edu.get('graduation')))}}}"
                + (f"\\\\[4pt]\n    {{\\small GPA: {esc(edu.get('gpa'))}}}"
                   if edu.get("gpa") else ""),
                "",
            ]

    certs = skills.get("certifications") or []
    if certs:
        out += ["    \\sideSection{Certifications}",
                "    \\begin{itemize}[leftmargin=0pt, label={--}, itemsep=2pt]"]
        for c in certs:
            out.append(f"      \\item {{\\small {esc(c)}}}")
        out += ["    \\end{itemize}", ""]

    langs = skills.get("languages") or []
    if langs:
        out += ["    \\sideSection{Languages}",
                "    \\begin{itemize}[leftmargin=0pt, label={}, itemsep=2pt]"]
        for lang in langs:
            out.append(f"      \\item {{\\small {esc(lang)}}}")
        out += ["    \\end{itemize}", ""]

    out += [
        "  \\end{minipage}",
        "\\end{minipage}%",
        "%",
        "% ---- Main Column --------------------------------------------",
        "\\begin{minipage}[t][\\paperheight][t]{\\mainW}",
        "  \\color{mainText}",
        "  \\hspace*{\\innerPad}\\begin{minipage}{\\mainW - 2\\innerPad}",
        "    \\vspace{\\innerPad}",
        "",
        "    \\mainSection{Experience}",
        "",
    ]
    for exp in profile.get("experience") or []:
        out.append(f"    \\expEntry{{{esc(exp.get('title'))}}}"
                   f"{{{esc(exp.get('company'))}}}"
                   f"{{{esc(date_range(exp))}}}{{{esc(exp.get('location', ''))}}}")
        bl = itemize(exp_bullets(exp),
                     "leftmargin=1.2em, itemsep=1pt, topsep=2pt")
        if bl:
            out.append("    " + bl.replace("\n", "\n    "))
        out.append("    \\vspace{6pt}")
        out.append("")

    projects = profile.get("projects") or []
    if projects:
        out += ["    \\mainSection{Projects}", ""]
        for proj in projects:
            url = strip_url(proj.get("url"))
            head = f"    \\textbf{{{esc(proj.get('name'))}}}"
            if url:
                head += (f" \\hfill\n    \\href{{https://{esc(url)}}}"
                         f"{{\\small\\color{{accentBlue}}{esc(url)}}}")
            out.append(head + "\\\\")
            desc = " ".join(str(x) for x in
                            (proj.get("description"), proj.get("impact")) if x)
            if desc:
                out.append(f"    {{\\small {esc(desc)}}}")
            out.append("    \\vspace{6pt}")
            out.append("")

    out += ["  \\end{minipage}", "\\end{minipage}", ""]
    return "\n".join(out)


def body_deedy(profile):
    p = profile.get("personal") or {}
    skills = profile.get("skills") or {}
    contact = ["\\href{mailto:\\resumeEmail}{\\resumeEmail}"]
    if p.get("phone"):
        contact.append("\\resumePhone")
    if p.get("linkedin"):
        contact.append("\\href{https://\\resumeLinkedIn}{\\resumeLinkedIn}")
    if p.get("github"):
        contact.append("\\href{https://\\resumeGitHub}{\\resumeGitHub}")
    out = [
        "% ---- Full-width Header --------------------------------------",
        "\\noindent",
        "\\begin{minipage}{\\textwidth}",
        "  \\centering",
        "  {\\namefont\\bfseries\\color{headerColor}\\resumeName}\\\\[4pt]",
        "  \\small",
        "  " + "\\quad|\\quad\n  ".join(contact),
        "\\end{minipage}",
        "\\vspace{8pt}",
        "",
        "\\noindent\\rule{\\textwidth}{0.8pt}",
        "\\vspace{4pt}",
        "",
        "% ---- Two-column body ----------------------------------------",
        "\\noindent",
        "\\begin{minipage}[t]{\\leftColW}",
        "",
    ]

    education = profile.get("education") or []
    if education:
        out.append("  \\lsection{Education}\n")
        for edu in education:
            grad = esc(fmt_date(edu.get("graduation")))
            gpa = f" | GPA {esc(edu['gpa'])}" if edu.get("gpa") else ""
            out += [
                f"  \\textbf{{\\small {esc(degree_line(edu))}}}\\\\",
                f"  {{\\small {esc(edu.get('institution'))}}}\\\\",
                f"  {{\\small\\color{{muted}}{grad}{gpa}}}\\\\[6pt]",
                "",
            ]

    links = []
    if p.get("portfolio"):
        links.append("    \\item \\href{https://\\resumeWebsite}{\\small\\resumeWebsite}")
    if p.get("github"):
        links.append("    \\item \\href{https://\\resumeGitHub}{\\small\\resumeGitHub}")
    if p.get("linkedin"):
        links.append("    \\item \\href{https://\\resumeLinkedIn}{\\small\\resumeLinkedIn}")
    if links:
        out += ["  \\lsection{Links}",
                "  \\begin{itemize}[leftmargin=0pt, label={}, itemsep=2pt]"]
        out += links
        out += ["  \\end{itemize}", ""]

    for label, vals in (("Core Skills", skills.get("technical")),
                        ("Technologies", skills.get("tools"))):
        vals = (vals or [])[:8]
        if vals:
            out += [f"  \\lsection{{{label}}}",
                    "  \\begin{itemize}[leftmargin=0pt, label={}, itemsep=1pt]"]
            for s in vals:
                out.append(f"    \\item {{\\small {esc(s)}}}")
            out += ["  \\end{itemize}", ""]

    out += [
        "\\end{minipage}%",
        "\\hspace{\\colSep}%",
        "\\begin{minipage}[t]{\\rightColW}",
        "",
        "  \\rsection{Experience}",
        "",
    ]
    for exp in profile.get("experience") or []:
        out.append(f"  \\rEntry{{{esc(exp.get('title'))}}}"
                   f"{{{esc(exp.get('company'))}}}"
                   f"{{{esc(date_range(exp))}}}{{{esc(exp.get('location', ''))}}}")
        bl = itemize(exp_bullets(exp), "leftmargin=1.2em, itemsep=1pt, topsep=2pt")
        if bl:
            out.append("  " + bl.replace("\n", "\n  "))
        out.append("  \\vspace{6pt}")
        out.append("")

    projects = profile.get("projects") or []
    if projects:
        out += ["  \\rsection{Projects}", ""]
        for proj in projects:
            url = strip_url(proj.get("url"))
            out.append(f"  \\noindent\\textbf{{{esc(proj.get('name'))}}}\\\\")
            desc = " ".join(str(x) for x in
                            (proj.get("description"), proj.get("impact")) if x)
            if desc:
                out.append(f"  {{\\small {esc(desc)}}}" + ("\\\\" if url else ""))
            if url:
                out.append(f"  \\href{{https://{esc(url)}}}{{\\small {esc(url)}}}")
            out.append("  \\vspace{6pt}")
            out.append("")

    out += ["\\end{minipage}", ""]
    return "\n".join(out)


def body_altacv(profile):
    p = profile.get("personal") or {}
    skills = profile.get("skills") or {}
    out = [
        "\\noindent",
        "% ---- Sidebar ------------------------------------------------",
        "\\begin{minipage}[t][\\paperheight][t]{\\sideW}",
        "  \\begin{tikzpicture}[remember picture, overlay]",
        "    \\fill[themeColor] (0,0) rectangle (\\sideW, -\\paperheight);",
        "  \\end{tikzpicture}",
        "  \\color{sideText}",
        "  \\hspace*{\\pad}\\begin{minipage}{\\sideW - 2\\pad}",
        "    \\vspace{\\pad}",
        "",
        "    % ---- Photo placeholder (no photo field in the profile) ---",
        "    \\begin{center}",
        "      \\begin{tikzpicture}",
        "        \\draw[themeLight, line width=2pt] (0,0) circle (1.2cm);",
        "        \\node[font=\\tiny\\color{sideText!60}] at (0,0) {Photo};",
        "      \\end{tikzpicture}",
        "    \\end{center}",
        "",
        "    \\begin{center}",
        "      {\\bfseries\\large\\color{white}\\resumeName}\\\\[2pt]",
        "      {\\small\\color{themeTag}\\resumeTitle}",
        "    \\end{center}",
        "",
        "    \\sideSection{Contact}",
        "    \\begin{itemize}[leftmargin=0pt, label={}, itemsep=3pt]",
    ]
    out += _sidebar_contact_items(p, website=True)
    out += ["    \\end{itemize}", ""]

    technical = (skills.get("technical") or [])[:6]
    if technical:
        out += ["    \\sideSection{Core Skills}",
                "    % NOTE: profile has no proficiency data; ratings default to 4/5"]
        for s in technical:
            out.append(f"    \\skillrating{{{esc(s)}}}{{4}}{{5}}")
        out.append("")

    tools = (skills.get("tools") or [])[:10]
    if tools:
        out += ["    \\sideSection{Tools}", "    \\vspace{2pt}"]
        for t in tools:
            out.append(f"    \\skilltag{{{esc(t)}}}")
        out.append("")

    langs = skills.get("languages") or []
    if langs:
        out.append("    \\sideSection{Languages}")
        for lang in langs:
            out.append(f"    \\skillrating{{{esc(lang)}}}{{4}}{{5}}")
        out.append("")

    out += [
        "  \\end{minipage}",
        "\\end{minipage}%",
        "%",
        "% ---- Main Column --------------------------------------------",
        "\\begin{minipage}[t][\\paperheight][t]{\\mainW}",
        "  \\color{mainText}",
        "  \\hspace*{\\pad}\\begin{minipage}{\\mainW - 2\\pad}",
        "    \\vspace{\\pad}",
        "",
    ]

    if profile.get("summary"):
        out += ["    \\mainSection{Profile}",
                f"    {esc(profile['summary'])}", ""]

    out += ["    \\mainSection{Experience}", ""]
    for exp in profile.get("experience") or []:
        out.append(f"    \\expEntry{{{esc(exp.get('title'))}}}"
                   f"{{{esc(exp.get('company'))}}}{{{esc(date_range(exp))}}}")
        bl = itemize(exp_bullets(exp), "leftmargin=1.2em, itemsep=1pt, topsep=2pt")
        if bl:
            out.append("    " + bl.replace("\n", "\n    "))
        out.append("    \\vspace{6pt}")
        out.append("")

    education = profile.get("education") or []
    if education:
        out += ["    \\mainSection{Education}", ""]
        for edu in education:
            out.append(f"    \\eduEntry{{{esc(degree_line(edu))}}}"
                       f"{{{esc(edu.get('institution'))}}}"
                       f"{{{esc(fmt_date(edu.get('graduation')))}}}")
            out.append("    \\vspace{4pt}")
        out.append("")

    out += ["  \\end{minipage}", "\\end{minipage}", ""]
    return "\n".join(out)


def body_awesome(profile):
    p = profile.get("personal") or {}
    skills = profile.get("skills") or {}
    icons = []
    if p.get("phone"):
        icons.append("  \\contactIcon{\\faPhone}{\\resumePhone}{tel:\\resumePhone}\\quad")
    icons.append("  \\contactIcon{\\faEnvelope}{\\resumeEmail}{mailto:\\resumeEmail}\\quad")
    if p.get("linkedin"):
        icons.append("  \\contactIcon{\\faLinkedin}{\\resumeLinkedIn}{https://\\resumeLinkedIn}\\quad")
    if p.get("github"):
        icons.append("  \\contactIcon{\\faGithub}{\\resumeGitHub}{https://\\resumeGitHub}\\quad")
    if p.get("portfolio"):
        icons.append("  \\contactIcon{\\faGlobe}{\\resumeWebsite}{https://\\resumeWebsite}\\quad")
    if p.get("location"):
        icons.append("  \\contactIcon{\\faMapMarker*}{\\resumeLocation}{}")
    if icons and icons[-1].endswith("\\quad"):
        icons[-1] = icons[-1][: -len("\\quad")]

    out = [
        "% ---- Header -------------------------------------------------",
        "\\begin{center}",
        "  {\\fontsize{34pt}{36pt}\\selectfont\\sffamily\\bfseries\\color{headerName}%",
        "    \\resumeFirstName\\ {\\color{themeRed}\\resumeLastName}}\\\\[4pt]",
        "  {\\large\\sffamily\\color{grayText}\\resumeSubtitle}\\\\[8pt]",
    ]
    out += icons
    out += [
        "\\end{center}",
        "",
        "\\vspace{2pt}",
        "\\noindent{\\color{themeRed}\\rule{\\textwidth}{1.5pt}}",
        "\\vspace{4pt}",
        "",
    ]

    if profile.get("summary"):
        out += ["\\section{Summary}", esc(profile["summary"]), ""]

    out += ["\\section{Experience}", ""]
    for exp in profile.get("experience") or []:
        out.append(f"\\cvEntry{{{esc(date_range(exp))}}}"
                   f"{{{esc(exp.get('company'))}}}"
                   f"{{{esc(exp.get('title'))}}}{{{esc(exp.get('location', ''))}}}")
        bl = itemize(exp_bullets(exp), "leftmargin=1.5em, itemsep=1pt, topsep=2pt")
        if bl:
            out.append(bl)
        out.append("\\vspace{6pt}")
        out.append("")

    education = profile.get("education") or []
    if education:
        out += ["\\section{Education}", ""]
        for edu in education:
            gpa = esc(edu.get("gpa") or "--")
            out.append(f"\\cvEduEntry{{{esc(fmt_date(edu.get('graduation')))}}}"
                       f"{{{esc(edu.get('institution'))}}}"
                       f"{{{esc(degree_line(edu))}}}{{{gpa}}}")
            out.append("\\vspace{4pt}")
        out.append("")

    rows = [("Technical", skills.get("technical")),
            ("Tools", skills.get("tools")),
            ("Languages", skills.get("languages")),
            ("Certifications", skills.get("certifications"))]
    rows = [(label, vals) for label, vals in rows if vals]
    if rows:
        out += ["\\section{Skills}", "", "\\noindent",
                "\\begin{tabularx}{\\textwidth}{@{}>{\\bfseries}l X@{}}"]
        for label, vals in rows:
            out.append(f"  {label} & {esc_join(vals)} \\\\")
        out += ["\\end{tabularx}", ""]

    return "\n".join(out)


BODY_BUILDERS = {
    "jakes-resume": body_jakes,
    "modern-professional": body_modern,
    "technical-clean": body_technical_clean,
    "deedy-resume": body_deedy,
    "altacv": body_altacv,
    "awesome-cv": body_awesome,
}


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def render(template_name, template_text, profile):
    begin = template_text.find("\\begin{document}")
    end = template_text.rfind("\\end{document}")
    if begin == -1 or end == -1:
        raise ValueError(
            f"template '{template_name}' has no \\begin{{document}}/\\end{{document}}")
    preamble = template_text[: begin + len("\\begin{document}")]
    preamble = fill_contact_macros(preamble, profile)
    body = BODY_BUILDERS[template_name](profile)
    return f"{preamble}\n\n{body}\n\\end{{document}}\n"


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "resume").lower()).strip("-")
    return slug or "resume"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Merge career-profile.json into a LaTeX resume template.")
    parser.add_argument("--template", required=True, choices=TEMPLATES)
    parser.add_argument("--profile", default="career-profile.json",
                        help="Path to career-profile.json (default: ./career-profile.json)")
    parser.add_argument("--output-dir", default="resumes",
                        help="Directory for the generated .tex (default: resumes/)")
    parser.add_argument("--templates-dir", default=None,
                        help="Directory containing the .tex templates "
                             "(default: <plugin>/templates/latex next to this script)")
    args = parser.parse_args(argv)

    templates_dir = (Path(args.templates_dir) if args.templates_dir
                     else Path(__file__).resolve().parent.parent / "templates" / "latex")
    template_path = templates_dir / f"{args.template}.tex"
    if not template_path.is_file():
        print(f"ERROR: template not found: {template_path}", file=sys.stderr)
        return 1

    try:
        with open(args.profile, "r", encoding="utf-8") as fh:
            profile = json.load(fh)
    except FileNotFoundError:
        print(f"ERROR: profile not found: {args.profile} — "
              "run the resume-updater skill first", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: {args.profile} is not valid JSON: {exc}", file=sys.stderr)
        return 1

    rendered = render(args.template, template_path.read_text(encoding="utf-8"),
                      profile)

    name_slug = slugify((profile.get("personal") or {}).get("name"))
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name_slug}-{args.template}.tex"
    out_path.write_text(rendered, encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
