/**
 * Locate standard item sections inside stripped SEC filing text.
 *
 * Filing text at this point is HTML-stripped and whitespace-collapsed, so
 * headings flow inline with body text ("... PART I Item 1A. Risk Factors The
 * Company's business ..."). Boundaries are found heuristically:
 *
 *  1. Title-confirmed pass — a candidate boundary is an item-number pattern
 *     ("Item 1A", tolerant of spacing/case) immediately followed, within
 *     TITLE_WINDOW characters, by the section's expected title words. Title
 *     confirmation is what disambiguates colliding item numbers (a 10-Q has
 *     both Part I "Item 1. Financial Statements" and Part II "Item 1. Legal
 *     Proceedings"). The section is the first confirmed start whose distance
 *     to the next confirmed end clears MIN_SECTION_CHARS — table-of-contents
 *     rows repeat every heading but with tiny spans, so they are skipped.
 *     A candidate whose span ends BEFORE a later confirmed start is showing
 *     the TOC signature (its "section" ended before the real heading even
 *     appeared) and must additionally clear TOC_SPAN_MAX: a TOC that nests
 *     sub-entries under an item (MSFT 10-Qs list a)–g) statement rows under
 *     Item 1) can exceed MIN_SECTION_CHARS but never approaches TOC_SPAN_MAX.
 *     Simply preferring the last confirmed start would not work: repeated
 *     in-section headings ("Item 1 NOTES TO FINANCIAL STATEMENTS") confirm
 *     too, and would truncate the front of the section.
 *  1b. Short-section pass — if every title-confirmed span falls below
 *     MIN_SECTION_CHARS, accept the last confirmed start bounded by a
 *     confirmed end. Genuinely short sections are the norm in some spots (a
 *     10-Q Part II legal-proceedings item is often a one-sentence
 *     cross-reference to a financial-statement note); a span with BOTH
 *     boundaries title-confirmed is a real section, not a TOC row.
 *  2. Fallback pass — if no title-confirmed span is found (nonstandard
 *     heading wording), retry on bare item numbers and take the longest
 *     span. Results from this pass are flagged `approximate`.
 *
 * When no end marker follows a start, the section runs to end-of-document.
 * Callers must treat a null result as "could not locate" and say so rather
 * than returning unrelated text.
 */

import type { FilingSectionKey } from "../constants.js";

export type SectionForm = "10-K" | "10-Q";

interface BoundaryPattern {
  item: string; // item number token: "1", "1a", "7a", ...
  title: RegExp; // expected heading words following the item number
}

interface SectionSpec {
  label: string;
  start: BoundaryPattern;
  ends: BoundaryPattern[];
}

// In a genuine heading (and in TOC rows) the title begins right after the
// item number, with at most punctuation between ("Item 1A. Risk Factors").
// Cross-references either put connective prose between them ("Item 1A of
// this Form 10-K under the heading Risk Factors") — rejected by requiring
// the title to start within TITLE_OFFSET chars — or quote the title inline
// ("in Part II, Item 8, Financial Statements and Supplementary Data of this
// Form 10-K") — rejected by the backward guard, since genuine headings are
// never preceded by a preposition + "Part I/II" or a bare referencing verb.
const TITLE_SEARCH = 90; // chars after the item number searched for the title
const TITLE_OFFSET = 12; // the title must begin within this many chars
const XREF_BEFORE =
  /\b(?:in|see|under|of|and|to|per|with|within)\s+part\s+[ivx]+[,.]?\s*$|\b(?:in|see|under|described\s+in|refer(?:\s+to)?|section\s+in|included\s+in|set\s+forth\s+in)\s*$/i;
const MIN_SECTION_CHARS = 250; // spans shorter than this are TOC rows, not sections
const TOC_SPAN_MAX = 2500; // TOC rows never span this much, even with nested sub-entries
const MIN_GAP = 40; // an end marker must be at least this far past the start

// Titles are matched letter-by-letter with optional intervening whitespace
// or apostrophes: HTML stripping can split words at element boundaries (a
// page break in MSFT's 10-K renders "RISK FACTORS" as "RIS K FACTORS"), and
// "Management's" may survive as "Management s" or "Management’s".
function titleRe(phrase: string): RegExp {
  const word = (w: string) => w.split("").join("[\\s'’]{0,2}");
  return new RegExp("\\b" + phrase.split(" ").map(word).join("[\\s'’]{1,3}"), "i");
}

const MDNA_TITLE = titleRe("managements discussion");
const RISK_TITLE = titleRe("risk factors");
const FIN_STMTS_TITLE = titleRe("financial statements");
const LEGAL_TITLE = titleRe("legal proceedings");
const MINE_TITLE = titleRe("mine safety");
const QUANT_TITLE = titleRe("quantitative and qualitative");
const CONTROLS_TITLE = titleRe("controls and procedures");
const UNRESOLVED_TITLE = titleRe("unresolved staff");
const EXHIBITS_TITLE = titleRe("exhibits");

const SPECS: Record<SectionForm, Partial<Record<FilingSectionKey, SectionSpec>>> = {
  "10-K": {
    business: {
      label: "Item 1 — Business",
      start: { item: "1", title: titleRe("business") },
      ends: [
        { item: "1a", title: RISK_TITLE },
        { item: "1b", title: UNRESOLVED_TITLE },
        { item: "2", title: titleRe("propert") },
      ],
    },
    risk_factors: {
      label: "Item 1A — Risk Factors",
      start: { item: "1a", title: RISK_TITLE },
      ends: [
        { item: "1b", title: UNRESOLVED_TITLE },
        { item: "1c", title: titleRe("cybersecurity") },
        { item: "2", title: titleRe("propert") },
      ],
    },
    legal_proceedings: {
      label: "Item 3 — Legal Proceedings",
      start: { item: "3", title: LEGAL_TITLE },
      ends: [
        { item: "4", title: MINE_TITLE },
        { item: "5", title: titleRe("market for") },
      ],
    },
    mdna: {
      label: "Item 7 — Management's Discussion and Analysis",
      start: { item: "7", title: MDNA_TITLE },
      ends: [
        { item: "7a", title: QUANT_TITLE },
        { item: "8", title: FIN_STMTS_TITLE },
      ],
    },
    financial_statements: {
      label: "Item 8 — Financial Statements and Supplementary Data",
      start: { item: "8", title: FIN_STMTS_TITLE },
      ends: [
        { item: "9", title: titleRe("changes in and disagreements") },
        { item: "9a", title: CONTROLS_TITLE },
      ],
    },
  },
  "10-Q": {
    financial_statements: {
      label: "Part I, Item 1 — Financial Statements",
      start: { item: "1", title: FIN_STMTS_TITLE },
      ends: [{ item: "2", title: MDNA_TITLE }],
    },
    mdna: {
      label: "Part I, Item 2 — Management's Discussion and Analysis",
      start: { item: "2", title: MDNA_TITLE },
      ends: [
        { item: "3", title: QUANT_TITLE },
        { item: "4", title: CONTROLS_TITLE },
      ],
    },
    legal_proceedings: {
      label: "Part II, Item 1 — Legal Proceedings",
      start: { item: "1", title: LEGAL_TITLE },
      ends: [
        { item: "1a", title: RISK_TITLE },
        { item: "2", title: titleRe("unregistered sales") },
        { item: "6", title: EXHIBITS_TITLE },
      ],
    },
    risk_factors: {
      label: "Part II, Item 1A — Risk Factors",
      start: { item: "1a", title: RISK_TITLE },
      ends: [
        { item: "2", title: titleRe("unregistered sales") },
        { item: "3", title: titleRe("defaults") },
        { item: "4", title: MINE_TITLE },
        { item: "5", title: titleRe("other information") },
        { item: "6", title: EXHIBITS_TITLE },
      ],
    },
    // business: a 10-Q has no Business section — the tool rejects the combination.
  },
};

// Matches "Item 1A", "ITEM 1a.", "Item 1 A" etc. The trailing \b keeps
// "Item 1" from matching "Item 1A"/"Item 10" (digit→letter/digit continues
// the word, so no boundary), which is why plain numbers need no lookahead.
function itemPattern(item: string): RegExp {
  const m = /^(\d+)([a-z])?$/i.exec(item);
  if (!m) throw new Error(`Invalid item token: ${item}`);
  const body = m[2] ? `${m[1]}\\s*${m[2]}` : m[1];
  return new RegExp(`\\bitem\\s*${body}\\b`, "gi");
}

function allPositions(text: string, re: RegExp): number[] {
  const out: number[] = [];
  for (const m of text.matchAll(re)) {
    out.push(m.index ?? 0);
  }
  return out;
}

function confirmedPositions(text: string, b: BoundaryPattern): number[] {
  const out: number[] = [];
  for (const m of text.matchAll(itemPattern(b.item))) {
    const idx = m.index ?? 0;
    const windowStart = idx + m[0].length;
    const title = b.title.exec(text.slice(windowStart, windowStart + TITLE_SEARCH));
    if (!title || title.index > TITLE_OFFSET) continue;
    if (XREF_BEFORE.test(text.slice(Math.max(0, idx - 40), idx))) continue;
    out.push(idx);
  }
  return out;
}

export interface LocatedSection {
  text: string;
  label: string;
  approximate: boolean; // true when the fallback (bare item number) pass was used
}

export function isSectionAvailable(section: FilingSectionKey, form: SectionForm): boolean {
  return Boolean(SPECS[form][section]);
}

export function extractSection(
  text: string,
  section: FilingSectionKey,
  form: SectionForm
): LocatedSection | null {
  const spec = SPECS[form][section];
  if (!spec) return null;

  // Pass 1: title-confirmed boundaries; first start clearing the TOC checks
  // wins. A TOC row can exceed MIN_SECTION_CHARS when the TOC nests
  // sub-entries under an item, but it always ends before a later confirmed
  // start (the genuine heading it foreshadows) — that signature demands the
  // far larger TOC_SPAN_MAX. A genuine heading followed by repeated
  // in-section headings ("Item 1 NOTES TO FINANCIAL STATEMENTS") keeps those
  // repeats inside its own span, so it never shows the signature.
  const starts = confirmedPositions(text, spec.start);
  const ends = spec.ends
    .flatMap((e) => confirmedPositions(text, e))
    .sort((a, b) => a - b);
  for (const s of starts) {
    const e = ends.find((p) => p > s + MIN_GAP) ?? text.length;
    const span = e - s;
    if (span < MIN_SECTION_CHARS) continue;
    if (span < TOC_SPAN_MAX && starts.some((s2) => s2 > e)) continue; // TOC signature
    return { text: text.slice(s, e), label: spec.label, approximate: false };
  }

  // Pass 1b: title-confirmed starts exist but every span is short. Genuinely
  // short sections are common (a 10-Q Part II "Legal Proceedings" is often a
  // one-sentence cross-reference to a note), and a short span whose start AND
  // end are both title-confirmed is a real section, not a TOC row — a TOC row
  // is either followed by the next TOC entry within MIN_GAP or superseded by
  // the later genuine heading, since we prefer the LAST confirmed start here.
  // Falling through to bare item numbers instead would return a different
  // section's text mislabeled as this one.
  for (let i = starts.length - 1; i >= 0; i--) {
    const s = starts[i];
    const e = ends.find((p) => p > s + MIN_GAP);
    if (e !== undefined) {
      return { text: text.slice(s, e), label: spec.label, approximate: false };
    }
  }

  // Pass 2: bare item numbers, longest span wins.
  const bareStarts = allPositions(text, itemPattern(spec.start.item));
  const bareEnds = spec.ends
    .flatMap((e) => allPositions(text, itemPattern(e.item)))
    .sort((a, b) => a - b);
  let best: { s: number; e: number } | null = null;
  for (const s of bareStarts) {
    const e = bareEnds.find((p) => p > s + MIN_GAP) ?? text.length;
    if (!best || e - s > best.e - best.s) best = { s, e };
  }
  if (best && best.e - best.s >= MIN_SECTION_CHARS) {
    return { text: text.slice(best.s, best.e), label: spec.label, approximate: true };
  }

  return null;
}
