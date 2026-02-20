import axios from "axios";
import * as cheerio from "cheerio";
import { RATE_LIMITS, USER_AGENT } from "../constants.js";
import type { JobListing } from "../types.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.indeed);

const INDEED_BASE_URL = "https://www.indeed.com/jobs";

function buildIndeedUrl(query: string, location?: string, remote?: boolean, start: number = 0): string {
  const params = new URLSearchParams();
  params.set("q", query);
  if (location) {
    params.set("l", location);
  }
  if (remote) {
    params.set("remotejob", "032b3046-06a3-4876-8dfd-474eb5e7ed11");
  }
  params.set("start", start.toString());
  return `${INDEED_BASE_URL}?${params.toString()}`;
}

function parseIndeedListings($: cheerio.CheerioAPI): JobListing[] {
  const listings: JobListing[] = [];

  try {
    $(".job_seen_beacon, .jobsearch-ResultsList .result, .resultContent").each((_index, element) => {
      try {
        const el = $(element);

        const titleEl = el.find("h2.jobTitle a, .jobTitle > a, a[data-jk]").first();
        const title = titleEl.text().trim();
        const relativeUrl = titleEl.attr("href") || "";
        const url = relativeUrl.startsWith("http") ? relativeUrl : `https://www.indeed.com${relativeUrl}`;

        const company = el.find("[data-testid='company-name'], .companyName, .company").first().text().trim();
        const location = el.find("[data-testid='text-location'], .companyLocation, .location").first().text().trim();

        const salaryEl = el.find(".salary-snippet-container, .salaryText, [data-testid='attribute_snippet_testid']").first();
        const salary = salaryEl.length > 0 ? salaryEl.text().trim() : null;

        const description = el.find(".job-snippet, .summary, [data-testid='jobDescriptionText']").first().text().trim();
        const dateEl = el.find(".date, .visually-hidden-date, span.css-qvloho").first();
        const posted_date = dateEl.length > 0 ? dateEl.text().trim() : null;

        if (title && company) {
          listings.push({
            title,
            company,
            location: location || "Not specified",
            salary,
            url,
            description: description || "No description available",
            posted_date,
            source: "indeed",
          });
        }
      } catch (innerErr) {
        console.error("Error parsing individual Indeed listing:", innerErr);
      }
    });
  } catch (err) {
    console.error("Error parsing Indeed results page:", err);
  }

  return listings;
}

export async function searchIndeedJobs(
  query: string,
  location?: string,
  remote?: boolean,
  limit: number = 10
): Promise<JobListing[]> {
  const allListings: JobListing[] = [];

  try {
    // Indeed shows ~15 results per page, fetch up to 2 pages if needed
    const pagesToFetch = Math.ceil(limit / 15);
    const maxPages = Math.min(pagesToFetch, 2);

    for (let page = 0; page < maxPages; page++) {
      if (allListings.length >= limit) break;

      const url = buildIndeedUrl(query, location, remote, page * 10);
      await limiter.acquire();

      const response = await axios.get(url, {
        headers: {
          "User-Agent": USER_AGENT,
          Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.9",
          "Accept-Encoding": "gzip, deflate, br",
        },
        timeout: 15_000,
        maxRedirects: 5,
      });

      const $ = cheerio.load(response.data);
      const pageListings = parseIndeedListings($);

      if (pageListings.length === 0) break;
      allListings.push(...pageListings);
    }
  } catch (err) {
    console.error("Indeed search error:", err instanceof Error ? err.message : String(err));
    if (allListings.length === 0) {
      return [{
        title: "[Indeed Search Error]",
        company: "Indeed",
        location: "N/A",
        salary: null,
        url: "https://www.indeed.com",
        description: `Failed to fetch results from Indeed: ${err instanceof Error ? err.message : String(err)}. The site may be blocking automated requests or the HTML structure may have changed.`,
        posted_date: null,
        source: "indeed",
      }];
    }
  }

  return allListings.slice(0, limit);
}
