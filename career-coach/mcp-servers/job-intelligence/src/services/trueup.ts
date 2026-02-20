import axios from "axios";
import * as cheerio from "cheerio";
import { RATE_LIMITS, USER_AGENT } from "../constants.js";
import type { JobListing, TrendingRole } from "../types.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.trueup);

const TRUEUP_BASE_URL = "https://www.trueup.io";
const TRUEUP_SEARCH_URL = `${TRUEUP_BASE_URL}/jobs`;
const TRUEUP_TRENDING_URL = `${TRUEUP_BASE_URL}/trending`;

export async function searchTrueUpJobs(
  query: string,
  limit: number = 10
): Promise<JobListing[]> {
  const listings: JobListing[] = [];

  try {
    const params = new URLSearchParams();
    params.set("search", query);
    const url = `${TRUEUP_SEARCH_URL}?${params.toString()}`;

    await limiter.acquire();

    const response = await axios.get(url, {
      headers: {
        "User-Agent": USER_AGENT,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
      },
      timeout: 15_000,
      maxRedirects: 5,
    });

    const $ = cheerio.load(response.data);

    // TrueUp job cards
    $("[class*='job-card'], [class*='JobCard'], .job-listing, tr[class*='job'], a[href*='/jobs/']").each((_index, element) => {
      if (listings.length >= limit) return;

      try {
        const el = $(element);

        const titleEl = el.find("h3, h4, [class*='title'], [class*='Title']").first();
        const title = titleEl.text().trim() || el.find("a").first().text().trim();

        const companyEl = el.find("[class*='company'], [class*='Company'], span:first-child").first();
        const company = companyEl.text().trim();

        const locationEl = el.find("[class*='location'], [class*='Location']").first();
        const location = locationEl.text().trim();

        const linkEl = el.is("a") ? el : el.find("a[href*='/jobs/']").first();
        const relativeUrl = linkEl.attr("href") || "";
        const jobUrl = relativeUrl.startsWith("http") ? relativeUrl : `${TRUEUP_BASE_URL}${relativeUrl}`;

        const salaryEl = el.find("[class*='salary'], [class*='Salary'], [class*='comp']").first();
        const salary = salaryEl.length > 0 ? salaryEl.text().trim() : null;

        if (title && company) {
          listings.push({
            title,
            company,
            location: location || "Not specified",
            salary,
            url: jobUrl,
            description: "View full description on TrueUp",
            posted_date: null,
            source: "trueup",
          });
        }
      } catch (innerErr) {
        console.error("Error parsing individual TrueUp listing:", innerErr);
      }
    });
  } catch (err) {
    console.error("TrueUp search error:", err instanceof Error ? err.message : String(err));
    if (listings.length === 0) {
      return [{
        title: "[TrueUp Search Error]",
        company: "TrueUp",
        location: "N/A",
        salary: null,
        url: TRUEUP_SEARCH_URL,
        description: `Failed to fetch results from TrueUp: ${err instanceof Error ? err.message : String(err)}. The site structure may have changed.`,
        posted_date: null,
        source: "trueup",
      }];
    }
  }

  return listings.slice(0, limit);
}

export async function getTrueUpTrendingRoles(
  industry?: string
): Promise<TrendingRole[]> {
  const roles: TrendingRole[] = [];

  try {
    const url = industry
      ? `${TRUEUP_TRENDING_URL}?industry=${encodeURIComponent(industry)}`
      : TRUEUP_TRENDING_URL;

    await limiter.acquire();

    const response = await axios.get(url, {
      headers: {
        "User-Agent": USER_AGENT,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
      },
      timeout: 15_000,
      maxRedirects: 5,
    });

    const $ = cheerio.load(response.data);

    // Parse trending role cards/rows
    $("[class*='trending'], [class*='Trending'], [class*='role-card'], table tbody tr, .card").each((_index, element) => {
      try {
        const el = $(element);

        const titleEl = el.find("h3, h4, td:first-child, [class*='title'], [class*='role']").first();
        const title = titleEl.text().trim();

        // Parse companies hiring
        const companiesText = el.find("[class*='companies'], [class*='Companies'], td:nth-child(2)").first().text().trim();
        const companies_hiring = companiesText
          ? companiesText.split(/[,|]/).map((c: string) => c.trim()).filter(Boolean)
          : [];

        const growthEl = el.find("[class*='growth'], [class*='Growth'], td:nth-child(3)").first();
        const growth_rate = growthEl.length > 0 ? growthEl.text().trim() : null;

        const salaryEl = el.find("[class*='salary'], [class*='Salary'], [class*='comp'], td:nth-child(4)").first();
        const avg_salary = salaryEl.length > 0 ? salaryEl.text().trim() : null;

        const demandEl = el.find("[class*='demand'], [class*='Demand'], td:nth-child(5)").first();
        const demandText = demandEl.text().trim().toLowerCase();
        let demand_level: "high" | "medium" | "low" | null = null;
        if (demandText.includes("high")) demand_level = "high";
        else if (demandText.includes("medium") || demandText.includes("moderate")) demand_level = "medium";
        else if (demandText.includes("low")) demand_level = "low";

        if (title) {
          roles.push({
            title,
            companies_hiring,
            growth_rate,
            avg_salary,
            demand_level,
          });
        }
      } catch (innerErr) {
        console.error("Error parsing individual TrueUp trending role:", innerErr);
      }
    });
  } catch (err) {
    console.error("TrueUp trending roles error:", err instanceof Error ? err.message : String(err));
    if (roles.length === 0) {
      return [{
        title: "[TrueUp Trending Error]",
        companies_hiring: [],
        growth_rate: null,
        avg_salary: null,
        demand_level: null,
      }];
    }
  }

  return roles;
}
