// Job board data sources — all use web scraping (no official APIs)
// Be conservative with rate limits to avoid blocks
export const RATE_LIMITS = {
    indeed: 0.2, // ~12 req/min — conservative
    linkedin: 0.1, // ~6 req/min — very conservative (aggressive blocking)
    glassdoor: 0.2, // ~12 req/min
    trueup: 0.5, // ~30 req/min — smaller site, more lenient
    levelsfyi: 0.2, // ~12 req/min
};
export const CHARACTER_LIMIT = 50_000;
export const MAX_JOB_RESULTS = 25;
export const MAX_SALARY_COMPARISONS = 10;
export const USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
//# sourceMappingURL=constants.js.map