import axios from "axios";
import * as cheerio from "cheerio";
import { RATE_LIMITS, USER_AGENT } from "../constants.js";
import { RateLimiter } from "./rate-limiter.js";
const limiter = new RateLimiter(RATE_LIMITS.levelsfyi);
const LEVELS_BASE_URL = "https://www.levels.fyi";
/**
 * Get salary/compensation data from Levels.fyi for a specific role.
 * Levels.fyi specializes in tech compensation with detailed level breakdowns.
 */
export async function getLevelsSalaryData(role, company, location) {
    const salaries = [];
    try {
        // Build search URL — Levels.fyi uses path-based search
        let searchPath = "/t";
        const roleLower = role.toLowerCase();
        // Map common roles to Levels.fyi paths
        if (roleLower.includes("software engineer")) {
            searchPath = "/t/software-engineer";
        }
        else if (roleLower.includes("product manager")) {
            searchPath = "/t/product-manager";
        }
        else if (roleLower.includes("data scientist")) {
            searchPath = "/t/data-scientist";
        }
        else if (roleLower.includes("designer") || roleLower.includes("ux")) {
            searchPath = "/t/product-designer";
        }
        else if (roleLower.includes("devops") || roleLower.includes("sre")) {
            searchPath = "/t/devops";
        }
        else if (roleLower.includes("data engineer")) {
            searchPath = "/t/data-engineer";
        }
        else if (roleLower.includes("machine learning") || roleLower.includes("ml")) {
            searchPath = "/t/machine-learning-engineer";
        }
        else if (roleLower.includes("frontend") || roleLower.includes("front-end")) {
            searchPath = "/t/front-end-engineer";
        }
        else if (roleLower.includes("backend") || roleLower.includes("back-end")) {
            searchPath = "/t/back-end-engineer";
        }
        else if (roleLower.includes("mobile") || roleLower.includes("ios") || roleLower.includes("android")) {
            searchPath = "/t/mobile-developer";
        }
        else if (roleLower.includes("security")) {
            searchPath = "/t/security-engineer";
        }
        else if (roleLower.includes("engineering manager")) {
            searchPath = "/t/engineering-manager";
        }
        else {
            // Fallback: slugify role
            const slug = role.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
            searchPath = `/t/${slug}`;
        }
        // Add company filter
        if (company) {
            const companySlug = company.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
            searchPath += `/c/${companySlug}`;
        }
        // Add location filter
        if (location) {
            const locationSlug = location.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
            searchPath += `/l/${locationSlug}`;
        }
        const url = `${LEVELS_BASE_URL}${searchPath}`;
        await limiter.acquire();
        const response = await axios.get(url, {
            headers: {
                "User-Agent": USER_AGENT,
                Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout: 15_000,
            maxRedirects: 5,
            validateStatus: (status) => status < 500,
        });
        const $ = cheerio.load(response.data);
        // Parse compensation data from Levels.fyi
        // They show compensation entries with base, stock, bonus breakdowns
        $("[class*='CompRow'], [class*='comp-row'], [class*='SalaryRow'], table tbody tr, [class*='entry']").each((_index, element) => {
            try {
                const el = $(element);
                const companyText = el.find("[class*='company'], [class*='Company'], td:nth-child(1) a, [data-test='company']").first().text().trim() || company || null;
                const levelText = el.find("[class*='level'], [class*='Level'], td:nth-child(2), [data-test='level']").first().text().trim() || null;
                const locationText = el.find("[class*='location'], [class*='Location'], td:nth-child(3), [data-test='location']").first().text().trim() || location || null;
                // Parse compensation components
                const totalText = el.find("[class*='total'], [class*='Total'], td:nth-child(4), [data-test='total-comp']").first().text().trim();
                const baseText = el.find("[class*='base'], [class*='Base'], td:nth-child(5), [data-test='base']").first().text().trim();
                const stockText = el.find("[class*='stock'], [class*='Stock'], [class*='equity'], td:nth-child(6), [data-test='stock']").first().text().trim();
                const bonusText = el.find("[class*='bonus'], [class*='Bonus'], td:nth-child(7), [data-test='bonus']").first().text().trim();
                const total_comp = parseDollarAmount(totalText);
                const base = parseDollarAmount(baseText);
                const equity = parseDollarAmount(stockText);
                const bonus = parseDollarAmount(bonusText);
                // Only add if we have at least some compensation data
                if (total_comp || base || companyText) {
                    salaries.push({
                        role,
                        company: companyText,
                        location: locationText,
                        base,
                        equity,
                        bonus,
                        total_comp: total_comp || (base && equity && bonus ? base + equity + bonus : base),
                        level: levelText,
                        source: "levelsfyi",
                    });
                }
            }
            catch (innerErr) {
                console.error("Error parsing individual Levels.fyi salary entry:", innerErr);
            }
        });
        // Also try parsing summary/aggregate data if individual entries not found
        if (salaries.length === 0) {
            try {
                // Look for summary compensation display
                const summaryTotal = $("[class*='median'], [class*='Median'], [class*='avg'], [class*='average']").first().text().trim();
                const summaryBase = $("[class*='baseMedian'], [class*='basePay']").first().text().trim();
                const summaryStock = $("[class*='stockMedian'], [class*='stockPay']").first().text().trim();
                const summaryBonus = $("[class*='bonusMedian'], [class*='bonusPay']").first().text().trim();
                if (summaryTotal || summaryBase) {
                    salaries.push({
                        role,
                        company: company || "Aggregate",
                        location: location || null,
                        base: parseDollarAmount(summaryBase),
                        equity: parseDollarAmount(summaryStock),
                        bonus: parseDollarAmount(summaryBonus),
                        total_comp: parseDollarAmount(summaryTotal),
                        level: "Median",
                        source: "levelsfyi",
                    });
                }
            }
            catch {
                // skip summary parse errors
            }
        }
    }
    catch (err) {
        console.error("Levels.fyi salary error:", err instanceof Error ? err.message : String(err));
        if (salaries.length === 0) {
            return [{
                    role,
                    company: company || null,
                    location: location || null,
                    base: null,
                    equity: null,
                    bonus: null,
                    total_comp: null,
                    level: null,
                    source: "levelsfyi",
                }];
        }
    }
    return salaries;
}
/**
 * Parse a dollar amount string (e.g., "$150,000", "$150K", "150000") into a number.
 */
function parseDollarAmount(text) {
    if (!text)
        return null;
    // Remove non-numeric characters except digits, commas, dots, and K/M
    const cleaned = text.replace(/[^0-9.,kKmM]/g, "").trim();
    if (!cleaned)
        return null;
    let multiplier = 1;
    let numStr = cleaned;
    if (cleaned.toLowerCase().endsWith("k")) {
        multiplier = 1000;
        numStr = cleaned.slice(0, -1);
    }
    else if (cleaned.toLowerCase().endsWith("m")) {
        multiplier = 1_000_000;
        numStr = cleaned.slice(0, -1);
    }
    const num = parseFloat(numStr.replace(/,/g, ""));
    if (isNaN(num))
        return null;
    return Math.round(num * multiplier);
}
//# sourceMappingURL=levelsfyi.js.map