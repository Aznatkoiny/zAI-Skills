export interface JobListing {
  title: string;
  company: string;
  location: string;
  salary: string | null;
  url: string;
  description: string;
  posted_date: string | null;
  source:
    | "indeed"
    | "trueup"
    | "remotive"
    | "remoteok"
    | "greenhouse"
    | "lever"
    | "adzuna"
    | "usajobs";
  /** Set when this entry is an error placeholder rather than a real listing. */
  error?: string;
}

// ── Per-source status reporting ──
//
// Every data service returns its items alongside a SourceMeta so tools can
// render an honest "Sources" footer: live / cached / skipped (no key) /
// failed (reason). "stale-cache" means the live fetch failed and an expired
// cache entry was served as graceful degradation.

export type SourceState = "live" | "cached" | "stale-cache" | "skipped" | "failed";

export interface SourceMeta {
  /** Display name, e.g. "Remotive" or "Greenhouse board (stripe)". */
  source: string;
  /** APIs are primary sources; scrapers are best-effort fallback. */
  tier: "api" | "scraper";
  state: SourceState;
  /** Items contributed (meaningful for live/cached/stale-cache). */
  count?: number;
  /** Cache entry age when state is cached/stale-cache. */
  ageMs?: number;
  /** Human-readable detail: skip reason or failure cause. */
  detail?: string;
}

export interface SourceResult<T> {
  meta: SourceMeta;
  items: T[];
}

export interface CompanyInfo {
  name: string;
  industry: string | null;
  size: string | null;
  rating: number | null;
  culture_ratings: Record<string, number> | null;
  interview_process: string | null;
  headquarters: string | null;
  founded: string | null;
  revenue: string | null;
  /** Set when the lookup failed (e.g. bot-blocked) rather than returning real data. */
  error?: string;
}

export interface SalaryData {
  role: string;
  company: string | null;
  location: string | null;
  base: number | null;
  equity: number | null;
  bonus: number | null;
  total_comp: number | null;
  level: string | null;
  source: "glassdoor" | "levelsfyi";
}

export interface InterviewExperience {
  company: string;
  role: string | null;
  difficulty: string | null;
  experience: "positive" | "neutral" | "negative" | null;
  questions: string[];
  process: string | null;
  offer: boolean | null;
  date: string | null;
}

export interface TrendingRole {
  title: string;
  companies_hiring: string[];
  growth_rate: string | null;
  avg_salary: string | null;
  demand_level: "high" | "medium" | "low" | null;
  /** Set when this entry is an error placeholder rather than a real role. */
  error?: string;
}
