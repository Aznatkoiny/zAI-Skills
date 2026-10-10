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
  version: "1.1.0",
});

// ── Tool Registration ──

server.tool(
  "job_search_jobs",
  "Search job listings. Returns a table of title, company, location, salary when posted, source and listing URL, plus a ~200-character snippet for the top 5 (open the URL for the full description). Sources: Remotive and RemoteOK (keyless; remote jobs only, location ignored), Adzuna (US) and USAJOBS (only when their API keys are set; these honor location), and the company's own Greenhouse/Lever board when the query names a well-known company. For a non-remote location, remote-only results are listed after location-matching ones. Indeed and TrueUp scrapers run only if the user set JOB_INTEL_ENABLE_SCRAPERS=1. Cached ~6h; the response ends with a per-source status footer (live / cached / skipped / failed). Use WebSearch when results are thin.",
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
  "Get a company's open roles from its public Greenhouse/Lever job board when it has one (about 30 well-known tech companies are mapped). Glassdoor ratings and company details are added only if the user set JOB_INTEL_ENABLE_SCRAPERS=1. Cached ~24h; the response ends with a per-source status footer. For company background, culture or news, use WebSearch.",
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
  "Get compensation data. From Levels.fyi (always on): median total compensation per level at a company (e.g. L3-L9), or, without a company or when it has no page, role-wide percentiles and the top-paying companies. Levels.fyi figures are total comp only (no base/stock/bonus split) and US-wide (no city filter); cite them as 'Data source: Levels.fyi'. Glassdoor base pay is added only if the user set JOB_INTEL_ENABLE_SCRAPERS=1. Cached ~24h; the response ends with a per-source status footer.",
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
  "Get interview experiences from Glassdoor (difficulty, questions asked, process, offer outcome). Works only if the user set JOB_INTEL_ENABLE_SCRAPERS=1; otherwise it returns a note saying the source is off, and you should use WebSearch for interview reports instead. Cached ~24h when enabled.",
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
  "Discover trending job roles from TrueUp (growth, salaries, hiring companies; global, no location filter). Works only if the user set JOB_INTEL_ENABLE_SCRAPERS=1; otherwise it returns a note saying the source is off, and you should use WebSearch for hiring-trend data instead. Cached ~6h when enabled.",
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
