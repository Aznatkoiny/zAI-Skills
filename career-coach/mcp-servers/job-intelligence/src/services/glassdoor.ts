import axios from "axios";
import * as cheerio from "cheerio";
import { RATE_LIMITS, USER_AGENT } from "../constants.js";
import type { CompanyInfo, SalaryData, InterviewExperience } from "../types.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.glassdoor);

const GLASSDOOR_BASE_URL = "https://www.glassdoor.com";

/**
 * Search for a company on Glassdoor and retrieve company overview information.
 */
export async function getGlassdoorCompanyInfo(
  company: string
): Promise<CompanyInfo | null> {
  try {
    // Search for the company
    const searchUrl = `${GLASSDOOR_BASE_URL}/Search/results.htm?keyword=${encodeURIComponent(company)}&typedKeyword=${encodeURIComponent(company)}&sc.keyword=${encodeURIComponent(company)}`;

    await limiter.acquire();

    const searchResponse = await axios.get(searchUrl, {
      headers: {
        "User-Agent": USER_AGENT,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
      },
      timeout: 15_000,
      maxRedirects: 5,
    });

    const $search = cheerio.load(searchResponse.data);

    // Try to find company overview link from search results
    const companyLink = $search("a[href*='/Overview/'], a[data-test='employer-short-name']").first().attr("href");
    let overviewUrl = companyLink
      ? (companyLink.startsWith("http") ? companyLink : `${GLASSDOOR_BASE_URL}${companyLink}`)
      : null;

    // If no search results, try direct URL pattern
    if (!overviewUrl) {
      const slug = company.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+/g, "-");
      overviewUrl = `${GLASSDOOR_BASE_URL}/Overview/Working-at-${slug}-EI_IE0.htm`;
    }

    await limiter.acquire();

    const overviewResponse = await axios.get(overviewUrl, {
      headers: {
        "User-Agent": USER_AGENT,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
      },
      timeout: 15_000,
      maxRedirects: 5,
      validateStatus: (status) => status < 500,
    });

    if (overviewResponse.status >= 400) {
      console.error(`Glassdoor company info returned status ${overviewResponse.status} for ${company}`);
      return {
        name: company,
        industry: null,
        size: null,
        rating: null,
        culture_ratings: null,
        interview_process: null,
        headquarters: null,
        founded: null,
        revenue: null,
      };
    }

    const $ = cheerio.load(overviewResponse.data);

    // Parse company overview
    const name = $("[data-test='employer-name'], h1.employer-name, h1").first().text().trim() || company;

    // Rating
    let rating: number | null = null;
    const ratingText = $("[data-test='rating-info'] .rating, .ratingNum, [class*='rating'] .num, [class*='Rating'] span").first().text().trim();
    if (ratingText) {
      const parsed = parseFloat(ratingText);
      if (!isNaN(parsed)) rating = parsed;
    }

    // Company details from info section
    const industry = extractDetail($, "Industry", "Type");
    const size = extractDetail($, "Size", "Employees");
    const headquarters = extractDetail($, "Headquarters", "Location");
    const founded = extractDetail($, "Founded", "Year");
    const revenue = extractDetail($, "Revenue", "Annual");

    // Culture ratings
    const culture_ratings: Record<string, number> = {};
    $("[class*='culture'] [class*='rating-row'], [data-test*='culture'] div, .subRatings div").each((_i, el) => {
      try {
        const label = $(el).find("[class*='label'], span:first-child").first().text().trim();
        const val = $(el).find("[class*='value'], span:last-child").first().text().trim();
        if (label && val) {
          const num = parseFloat(val);
          if (!isNaN(num)) culture_ratings[label] = num;
        }
      } catch {
        // skip individual rating parse errors
      }
    });

    return {
      name,
      industry,
      size,
      rating,
      culture_ratings: Object.keys(culture_ratings).length > 0 ? culture_ratings : null,
      interview_process: null,
      headquarters,
      founded,
      revenue,
    };
  } catch (err) {
    console.error("Glassdoor company info error:", err instanceof Error ? err.message : String(err));
    return {
      name: company,
      industry: null,
      size: null,
      rating: null,
      culture_ratings: null,
      interview_process: `Error fetching company info: ${err instanceof Error ? err.message : String(err)}`,
      headquarters: null,
      founded: null,
      revenue: null,
    };
  }
}

function extractDetail($: cheerio.CheerioAPI, ...labels: string[]): string | null {
  for (const label of labels) {
    try {
      const el = $(`[class*='infoEntity']:contains("${label}"), dt:contains("${label}"), th:contains("${label}")`).first();
      if (el.length > 0) {
        const value = el.next("dd, td, span, [class*='value']").first().text().trim()
          || el.parent().find("[class*='value'], dd, td").first().text().trim();
        if (value) return value;
      }
    } catch {
      // skip
    }
  }
  return null;
}

/**
 * Get salary data for a specific role from Glassdoor.
 */
export async function getGlassdoorSalaries(
  role: string,
  company?: string
): Promise<SalaryData[]> {
  const salaries: SalaryData[] = [];

  try {
    const searchQuery = company ? `${role} ${company}` : role;
    const searchUrl = `${GLASSDOOR_BASE_URL}/Salaries/know-your-worth.htm?keyword=${encodeURIComponent(searchQuery)}`;

    await limiter.acquire();

    const response = await axios.get(searchUrl, {
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

    // Parse salary results
    $("[data-test='salaries-list'] li, [class*='SalaryCard'], [class*='salary-card'], .salaryList .salary-row, table tbody tr").each((_index, element) => {
      try {
        const el = $(element);

        const roleText = el.find("[class*='title'], h3, td:first-child, [data-test='salary-title']").first().text().trim() || role;
        const companyText = el.find("[class*='company'], [data-test='company-name'], td:nth-child(2)").first().text().trim() || company || null;

        // Try to parse salary figures
        const payText = el.find("[class*='pay'], [class*='salary'], [data-test='salary-amount'], td:nth-child(3)").first().text().trim();
        const baseMatch = payText.match(/\$?([\d,]+)/);
        const base = baseMatch ? parseInt(baseMatch[1].replace(/,/g, ""), 10) : null;

        // Additional compensation components
        const bonusText = el.find("[class*='bonus'], [class*='additional']").first().text().trim();
        const bonusMatch = bonusText.match(/\$?([\d,]+)/);
        const bonus = bonusMatch ? parseInt(bonusMatch[1].replace(/,/g, ""), 10) : null;

        const total_comp = base && bonus ? base + bonus : base;

        if (roleText) {
          salaries.push({
            role: roleText,
            company: companyText,
            location: null,
            base,
            equity: null,
            bonus,
            total_comp,
            level: null,
            source: "glassdoor",
          });
        }
      } catch (innerErr) {
        console.error("Error parsing individual Glassdoor salary:", innerErr);
      }
    });
  } catch (err) {
    console.error("Glassdoor salary error:", err instanceof Error ? err.message : String(err));
    if (salaries.length === 0) {
      return [{
        role,
        company: company || null,
        location: null,
        base: null,
        equity: null,
        bonus: null,
        total_comp: null,
        level: null,
        source: "glassdoor",
      }];
    }
  }

  return salaries;
}

/**
 * Get interview experiences from Glassdoor for a specific company.
 */
export async function getGlassdoorInterviews(
  company: string,
  role?: string
): Promise<InterviewExperience[]> {
  const experiences: InterviewExperience[] = [];

  try {
    const searchQuery = role ? `${company} ${role} interview` : `${company} interview`;
    const searchUrl = `${GLASSDOOR_BASE_URL}/Interview/index.htm?sc.keyword=${encodeURIComponent(searchQuery)}`;

    await limiter.acquire();

    const response = await axios.get(searchUrl, {
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

    // Parse interview experiences
    $("[class*='InterviewCard'], [class*='interview-card'], .interview, [data-test='interview-review']").each((_index, element) => {
      try {
        const el = $(element);

        const roleText = el.find("[class*='role'], [class*='title'], h3").first().text().trim() || role || null;

        // Difficulty
        const difficultyText = el.find("[class*='difficulty'], [data-test='difficulty']").first().text().trim();
        const difficulty = difficultyText || null;

        // Experience (positive/neutral/negative)
        const experienceText = el.find("[class*='experience'], [data-test='experience']").first().text().trim().toLowerCase();
        let experience: "positive" | "neutral" | "negative" | null = null;
        if (experienceText.includes("positive")) experience = "positive";
        else if (experienceText.includes("negative")) experience = "negative";
        else if (experienceText.includes("neutral") || experienceText.includes("mixed")) experience = "neutral";

        // Questions
        const questions: string[] = [];
        el.find("[class*='question'], li, [data-test='interview-question']").each((_qi, qEl) => {
          const q = $(qEl).text().trim();
          if (q && q.length > 10 && q.length < 500) {
            questions.push(q);
          }
        });

        // Process description
        const processText = el.find("[class*='process'], [class*='description'], [data-test='interview-process'], p").first().text().trim();
        const process = processText || null;

        // Offer status
        const offerText = el.find("[class*='offer'], [data-test='offer']").first().text().trim().toLowerCase();
        let offer: boolean | null = null;
        if (offerText.includes("accepted") || offerText.includes("received") || offerText.includes("yes")) offer = true;
        else if (offerText.includes("declined") || offerText.includes("rejected") || offerText.includes("no")) offer = false;

        // Date
        const dateText = el.find("[class*='date'], time").first().text().trim();
        const date = dateText || null;

        experiences.push({
          company,
          role: roleText,
          difficulty,
          experience,
          questions,
          process,
          offer,
          date,
        });
      } catch (innerErr) {
        console.error("Error parsing individual Glassdoor interview:", innerErr);
      }
    });
  } catch (err) {
    console.error("Glassdoor interview error:", err instanceof Error ? err.message : String(err));
    if (experiences.length === 0) {
      return [{
        company,
        role: role || null,
        difficulty: null,
        experience: null,
        questions: [],
        process: `Error fetching interview experiences: ${err instanceof Error ? err.message : String(err)}`,
        offer: null,
        date: null,
      }];
    }
  }

  return experiences;
}
