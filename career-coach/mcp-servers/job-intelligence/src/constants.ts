// Data-source configuration.
//
// The server is API-first: keyless public JSON APIs (Remotive, RemoteOK,
// Greenhouse/Lever boards, Levels.fyi's markdown routes) and keyed APIs
// (Adzuna, USAJOBS — skipped when env keys are unset) are the primary sources.
// HTML scrapers (Indeed, TrueUp, Glassdoor) are OFF by default: several of
// these sites' robots.txt or terms restrict automated access, so the user must
// opt in with JOB_INTEL_ENABLE_SCRAPERS=1. LinkedIn was removed entirely
// (its robots.txt and User Agreement prohibit it).

export const RATE_LIMITS = {
  // Scrapers — conservative to avoid blocks
  indeed: 0.2,      // ~12 req/min — conservative
  glassdoor: 0.2,   // ~12 req/min
  trueup: 0.5,      // ~30 req/min — smaller site, more lenient
  levelsfyi: 0.2,   // ~12 req/min
  // Public APIs — still polite; responses are cached (see services/cache.ts)
  remotive: 1 / 30, // Remotive blocks >2 req/min; the whole feed is fetched once per 6h anyway
  remoteok: 0.5,
  greenhouse: 1,
  lever: 1,
  adzuna: 0.4,      // free tier allows 25 hits/min, 250/day
  usajobs: 1,
} as const;

export const CHARACTER_LIMIT = 50_000;
export const MAX_JOB_RESULTS = 25;
export const MAX_SALARY_COMPARISONS = 10;

// Honest, self-identifying UA for every request, scrapers included: sites set
// their policy for automated agents in robots.txt, and impersonating a browser
// to get around that isn't something this server does.
export const API_USER_AGENT = "job-intelligence-mcp/1.1 (career-coach Claude plugin; +https://github.com/Aznatkoiny/zAI-Skills)";
export const USER_AGENT = API_USER_AGENT;

// HTML scrapers run only when the user opts in.
export const SCRAPERS_ENABLED = process.env.JOB_INTEL_ENABLE_SCRAPERS === "1";
export const SCRAPERS_DISABLED_DETAIL =
  "scraper off by default — set JOB_INTEL_ENABLE_SCRAPERS=1 to enable (check the site's terms first)";
