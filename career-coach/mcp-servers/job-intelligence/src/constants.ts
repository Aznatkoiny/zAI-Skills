// Data-source configuration.
//
// The server is API-first: keyless public JSON APIs (Remotive, RemoteOK,
// Greenhouse/Lever boards) and keyed APIs (Adzuna, USAJOBS — skipped when env
// keys are unset) are the primary sources. HTML scrapers (Indeed, LinkedIn,
// TrueUp, Glassdoor, Levels.fyi) remain as best-effort fallback and may be
// bot-blocked at any time. Be conservative with scraper rate limits.

export const RATE_LIMITS = {
  // Scrapers — conservative to avoid blocks
  indeed: 0.2,      // ~12 req/min — conservative
  linkedin: 0.1,    // ~6 req/min — very conservative (aggressive blocking)
  glassdoor: 0.2,   // ~12 req/min
  trueup: 0.5,      // ~30 req/min — smaller site, more lenient
  levelsfyi: 0.2,   // ~12 req/min
  // Public APIs — still polite; responses are cached (see services/cache.ts)
  remotive: 0.5,    // Remotive asks integrators not to poll aggressively
  remoteok: 0.5,
  greenhouse: 1,
  lever: 1,
  adzuna: 1,
  usajobs: 1,
} as const;

export const CHARACTER_LIMIT = 50_000;
export const MAX_JOB_RESULTS = 25;
export const MAX_SALARY_COMPARISONS = 10;

// Keep this roughly in sync with current stable Chrome — a stale UA is an easy bot signal.
// Used only by the HTML scrapers.
export const USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36";

// Honest, self-identifying UA for public JSON APIs (RemoteOK in particular
// rejects generic/empty agents and asks integrators to identify themselves).
export const API_USER_AGENT = "job-intelligence-mcp/1.0 (career-coach Claude plugin; +https://github.com/Aznatkoiny/zAI-Skills)";
