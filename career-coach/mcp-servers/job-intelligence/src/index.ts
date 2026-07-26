#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  searchJobsSchema,
  companyInfoSchema,
  salaryDataSchema,
  interviewExperiencesSchema,
  trendingRolesSchema,
} from "./schemas/inputs.js";
import { handleSearchJobs } from "./tools/search-jobs.js";
import { handleCompanyInfo } from "./tools/company-info.js";
import { handleSalaryData } from "./tools/salary-data.js";
import { handleInterviewExperiences } from "./tools/interview-experiences.js";
import { handleTrendingRoles } from "./tools/trending-roles.js";

const server = new McpServer({
  name: "job-intelligence",
  version: "1.0.0",
});

// ── Tool Registration ──

server.tool(
  "job_search_jobs",
  "Search job listings, API-first: Remotive and RemoteOK (keyless public APIs), Adzuna and USAJOBS (only when API keys are configured — otherwise skipped with a note), and the company's public Greenhouse/Lever board when the query names a well-known company. Indeed/LinkedIn/TrueUp scrapers run as best-effort fallback and may be bot-blocked. Results are deduplicated, cached (~6h), and every response ends with a per-source status footer (live / cached / skipped / failed). Fall back to WebSearch if all sources fail.",
  searchJobsSchema.shape,
  async (input) => {
    try {
      const text = await handleSearchJobs(input);
      return { content: [{ type: "text" as const, text }] };
    } catch (err) {
      return {
        content: [{ type: "text" as const, text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
        isError: true,
      };
    }
  }
);

server.tool(
  "job_get_company_info",
  "Get company overview, ratings, culture scores, and interview process from Glassdoor (scraper — may bot-block), plus live open roles from the company's public Greenhouse/Lever job board when one exists (API). Results are cached (~24h) and the response ends with a per-source status footer — fall back to WebSearch if sources fail.",
  companyInfoSchema.shape,
  async (input) => {
    try {
      const text = await handleCompanyInfo(input);
      return { content: [{ type: "text" as const, text }] };
    } catch (err) {
      return {
        content: [{ type: "text" as const, text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
        isError: true,
      };
    }
  }
);

server.tool(
  "job_get_salary_data",
  "Get salary and total compensation data from Glassdoor and Levels.fyi. Includes base pay, equity, bonus, and total comp breakdowns by level. Scraper-backed: sites may bot-block, so results can be partial. Results are cached (~24h) and the response ends with a per-source status footer — fall back to WebSearch if sources fail.",
  salaryDataSchema.shape,
  async (input) => {
    try {
      const text = await handleSalaryData(input);
      return { content: [{ type: "text" as const, text }] };
    } catch (err) {
      return {
        content: [{ type: "text" as const, text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
        isError: true,
      };
    }
  }
);

server.tool(
  "job_get_interview_experiences",
  "Get interview experiences from Glassdoor including difficulty ratings, questions asked, interview process descriptions, and offer outcomes. Scraper-backed: Glassdoor may bot-block, so results can be partial. Results are cached (~24h) and the response ends with a per-source status footer — fall back to WebSearch if it fails.",
  interviewExperiencesSchema.shape,
  async (input) => {
    try {
      const text = await handleInterviewExperiences(input);
      return { content: [{ type: "text" as const, text }] };
    } catch (err) {
      return {
        content: [{ type: "text" as const, text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
        isError: true,
      };
    }
  }
);

server.tool(
  "job_search_trending_roles",
  "Discover trending job roles from TrueUp with growth rates, average salaries, demand levels, and which companies are hiring. Results are global (TrueUp has no location filter). Scraper-backed: the site may bot-block, so results can be partial. Results are cached (~6h) and the response ends with a per-source status footer — fall back to WebSearch if it fails.",
  trendingRolesSchema.shape,
  async (input) => {
    try {
      const text = await handleTrendingRoles(input);
      return { content: [{ type: "text" as const, text }] };
    } catch (err) {
      return {
        content: [{ type: "text" as const, text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
        isError: true,
      };
    }
  }
);

// ── Server Startup ──

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Job Intelligence MCP Server started (stdio transport)");
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
