/**
 * Levels.fyi — compensation data from the site's LLM-readable markdown routes.
 *
 * Levels.fyi's robots.txt invites agents to append `.md` to salary routes
 * (e.g. /companies/google/salaries/software-engineer.md, /t/software-engineer.md)
 * and asks for attribution ("Data source: Levels.fyi"). This replaces the old
 * HTML scraper: the markdown is stable, sanctioned, and parsed without CSS
 * selectors. The pages report TOTAL compensation only (median per level for a
 * company; percentiles across companies for a role) — not base/stock/bonus.
 * Figures are US-wide; the pages have no city filter. Cached 24h.
 */

import axios from "axios";
import { API_USER_AGENT, RATE_LIMITS } from "../constants.js";
import type { SalaryData, SourceResult } from "../types.js";
import { fetchWithCache, LOOKUP_TTL_MS, toSourceResult } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.levelsfyi);

const LEVELS_BASE_URL = "https://www.levels.fyi";

function slugify(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
}

/** Map a free-text role to a Levels.fyi role slug (word-boundary matches). */
export function roleSlug(role: string): string {
  const r = role.toLowerCase();
  // Slugs checked against levels.fyi/t/<slug>.md (October 2026).
  const rules: Array<[RegExp, string]> = [
    [/engineering manager/, "software-engineering-manager"],
    [/\b(machine learning|ml)\b/, "machine-learning-engineer"],
    [/data scientist/, "data-scientist"],
    [/data engineer/, "data-engineer"],
    [/technical program manager|\btpm\b/, "technical-program-manager"],
    [/product manager/, "product-manager"],
    [/\b(designer|ux)\b/, "product-designer"],
    [/\b(sre|site reliability|devops)\b/, "site-reliability-engineer"],
    [/\bsecurity\b/, "security-engineer"],
    [/solutions? architect/, "solution-architect"],
    [/\b(software|backend|back-end|frontend|front-end|full[- ]?stack|mobile|ios|android)\b.*\b(engineer|developer)\b|\bswe\b/, "software-engineer"],
  ];
  for (const [pattern, slug] of rules) {
    if (pattern.test(r)) return slug;
  }
  return slugify(role);
}

function parseDollar(text: string): number | null {
  const m = text.replace(/,/g, "").match(/\$?\s*(\d+(?:\.\d+)?)\s*([kKmM])?/);
  if (!m) return null;
  let value = parseFloat(m[1]);
  const suffix = m[2]?.toLowerCase();
  if (suffix === "k") value *= 1_000;
  else if (suffix === "m") value *= 1_000_000;
  return Math.round(value);
}

/** Rows of the first markdown table under a `### heading`. */
function tableUnder(markdown: string, heading: string): string[][] {
  const start = markdown.indexOf(`### ${heading}`);
  if (start === -1) return [];
  const rows: string[][] = [];
  for (const line of markdown.slice(start).split("\n").slice(1)) {
    if (line.startsWith("|")) {
      const cells = line.split("|").slice(1, -1).map((c) => c.trim());
      if (cells.every((c) => /^-+$/.test(c))) continue; // separator row
      rows.push(cells);
    } else if (rows.length > 0) {
      break;
    }
  }
  return rows.slice(1); // drop header row
}

function highlight(markdown: string, label: string): number | null {
  const m = markdown.match(new RegExp(`^- ${label}:\\s*([^\\n]+)$`, "m"));
  return m ? parseDollar(m[1]) : null;
}

async function fetchMarkdown(path: string): Promise<string | null> {
  await limiter.acquire();
  const response = await axios.get(`${LEVELS_BASE_URL}${path}`, {
    headers: { "User-Agent": API_USER_AGENT, Accept: "text/markdown" },
    timeout: 15_000,
    maxRedirects: 3,
    validateStatus: (status) => status < 500,
  });
  if (response.status === 404) return null;
  if (response.status >= 400) throw new Error(`HTTP ${response.status}`);
  return String(response.data);
}

async function fetchLevelsSalaryData(role: string, company?: string): Promise<SalaryData[]> {
  const slug = roleSlug(role);
  const salaries: SalaryData[] = [];

  if (company) {
    const md = await fetchMarkdown(`/companies/${slugify(company)}/salaries/${slug}.md`);
    if (md) {
      for (const [level, comp] of tableUnder(md, "Levels Breakdown")) {
        const total = parseDollar(comp);
        if (total !== null) {
          salaries.push({ role, company, location: "United States", base: null, equity: null, bonus: null, total_comp: total, level, source: "levelsfyi" });
        }
      }
      const median = highlight(md, "Median Total Compensation");
      if (median !== null) {
        salaries.push({ role, company, location: "United States", base: null, equity: null, bonus: null, total_comp: median, level: "All levels (median)", source: "levelsfyi" });
      }
    }
  }

  // Role-wide figures: used when no company was given, or the company page had no data.
  if (salaries.length === 0) {
    const md = await fetchMarkdown(`/t/${slug}.md`);
    if (md) {
      const points: Array<[string, string]> = [
        ["Median Total Compensation", "Median, all companies"],
        ["90th Percentile", "90th percentile, all companies"],
      ];
      for (const [label, levelName] of points) {
        const value = highlight(md, label);
        if (value !== null) {
          salaries.push({ role, company: null, location: "United States", base: null, equity: null, bonus: null, total_comp: value, level: levelName, source: "levelsfyi" });
        }
      }
      const quartiles = md.match(/^- 25th \/ 75th Percentile:\s*([^/\n]+)\/\s*([^\n]+)$/m);
      if (quartiles) {
        const p25 = parseDollar(quartiles[1]);
        const p75 = parseDollar(quartiles[2]);
        if (p25 !== null) salaries.push({ role, company: null, location: "United States", base: null, equity: null, bonus: null, total_comp: p25, level: "25th percentile, all companies", source: "levelsfyi" });
        if (p75 !== null) salaries.push({ role, company: null, location: "United States", base: null, equity: null, bonus: null, total_comp: p75, level: "75th percentile, all companies", source: "levelsfyi" });
      }
      for (const [, companyName, comp] of tableUnder(md, "Top Paying Companies").slice(0, 5)) {
        const total = parseDollar(comp ?? "");
        if (companyName && total !== null) {
          salaries.push({ role, company: companyName, location: "United States", base: null, equity: null, bonus: null, total_comp: total, level: "Median (top-paying company)", source: "levelsfyi" });
        }
      }
    }
  }

  if (salaries.length === 0) {
    throw new Error(`no Levels.fyi data for role "${slug}"${company ? ` at ${company}` : ""}`);
  }
  return salaries;
}

/**
 * Total-compensation data from Levels.fyi (cached 24h). Never throws —
 * failures land in meta.
 */
export async function getLevelsSalaryData(role: string, company?: string): Promise<SourceResult<SalaryData>> {
  const res = await fetchWithCache(
    "levelsfyi-md",
    { role: role.toLowerCase().trim(), company: company?.toLowerCase().trim() || null },
    LOOKUP_TTL_MS,
    () => fetchLevelsSalaryData(role, company)
  );
  return toSourceResult("Levels.fyi", "api", res);
}
