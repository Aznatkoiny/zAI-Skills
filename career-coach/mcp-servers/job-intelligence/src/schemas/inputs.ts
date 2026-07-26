import { z } from "zod";
import { MAX_JOB_RESULTS } from "../constants.js";

export const searchJobsSchema = z.object({
  query: z.string().describe("Job search query (e.g., 'Senior Software Engineer')"),
  location: z.string().optional().describe("Location filter (e.g., 'San Francisco, CA' or 'Remote')"),
  remote: z.boolean().optional().default(false).describe("Filter for remote-only positions"),
  salary_min: z.number().optional().describe("Minimum annual salary filter in USD (hourly listings are annualized at 40h/week before comparison)"),
  experience_level: z.enum(["entry", "mid", "senior", "lead", "executive"]).optional().describe("Experience level filter"),
  limit: z.number().int().min(1).max(MAX_JOB_RESULTS).optional().default(10).describe("Maximum number of results (default 10)"),
});

export const companyInfoSchema = z.object({
  company_name: z.string().describe("Company name to look up (e.g., 'Google', 'Stripe')"),
});

export const salaryDataSchema = z.object({
  role: z.string().describe("Job role to look up salary data for (e.g., 'Software Engineer')"),
  company: z.string().optional().describe("Specific company to filter by"),
  location: z.string().optional().describe("Location to filter by"),
});

export const interviewExperiencesSchema = z.object({
  company_name: z.string().describe("Company name to look up interview experiences for"),
  role: z.string().optional().describe("Specific role to filter by"),
});

// Note: no location parameter — TrueUp trending data has no location filter,
// so results are always global.
export const trendingRolesSchema = z.object({
  industry: z.string().optional().describe("Industry to filter by (e.g., 'AI/ML', 'FinTech', 'Healthcare')"),
});
