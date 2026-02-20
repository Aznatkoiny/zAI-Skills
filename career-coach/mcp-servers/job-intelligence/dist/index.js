#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { searchJobsSchema, companyInfoSchema, salaryDataSchema, interviewExperiencesSchema, trendingRolesSchema, } from "./schemas/inputs.js";
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
server.tool("job_search_jobs", "Search for job listings across Indeed, LinkedIn, and TrueUp. Aggregates and deduplicates results from multiple sources.", searchJobsSchema.shape, async (input) => {
    try {
        const text = await handleSearchJobs(input);
        return { content: [{ type: "text", text }] };
    }
    catch (err) {
        return {
            content: [{ type: "text", text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
            isError: true,
        };
    }
});
server.tool("job_get_company_info", "Get company overview, ratings, culture scores, and interview process from Glassdoor. Includes industry, size, headquarters, and employee ratings.", companyInfoSchema.shape, async (input) => {
    try {
        const text = await handleCompanyInfo(input);
        return { content: [{ type: "text", text }] };
    }
    catch (err) {
        return {
            content: [{ type: "text", text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
            isError: true,
        };
    }
});
server.tool("job_get_salary_data", "Get salary and total compensation data from Glassdoor and Levels.fyi. Includes base pay, equity, bonus, and total comp breakdowns by level.", salaryDataSchema.shape, async (input) => {
    try {
        const text = await handleSalaryData(input);
        return { content: [{ type: "text", text }] };
    }
    catch (err) {
        return {
            content: [{ type: "text", text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
            isError: true,
        };
    }
});
server.tool("job_get_interview_experiences", "Get interview experiences from Glassdoor including difficulty ratings, questions asked, interview process descriptions, and offer outcomes.", interviewExperiencesSchema.shape, async (input) => {
    try {
        const text = await handleInterviewExperiences(input);
        return { content: [{ type: "text", text }] };
    }
    catch (err) {
        return {
            content: [{ type: "text", text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
            isError: true,
        };
    }
});
server.tool("job_search_trending_roles", "Discover trending job roles from TrueUp with growth rates, average salaries, demand levels, and which companies are hiring.", trendingRolesSchema.shape, async (input) => {
    try {
        const text = await handleTrendingRoles(input);
        return { content: [{ type: "text", text }] };
    }
    catch (err) {
        return {
            content: [{ type: "text", text: `Error: ${err instanceof Error ? err.message : String(err)}` }],
            isError: true,
        };
    }
});
// ── Server Startup ──
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("Job Intelligence MCP Server started (stdio transport)");
}
main().catch((err) => {
    console.error("Fatal error:", err);
    process.exit(1);
});
//# sourceMappingURL=index.js.map