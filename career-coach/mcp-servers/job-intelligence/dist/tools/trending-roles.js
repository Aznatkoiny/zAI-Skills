import { getTrueUpTrendingRoles } from "../services/trueup.js";
import { CHARACTER_LIMIT } from "../constants.js";
export async function handleTrendingRoles(input) {
    const { industry, location } = input;
    // Note: TrueUp trending page does not support location-based filtering.
    // The location parameter is included in the output header for context only.
    const roles = await getTrueUpTrendingRoles(industry);
    const lines = [
        `## Trending Roles${industry ? ` in ${industry}` : ""}`,
        "",
    ];
    if (industry)
        lines.push(`**Industry:** ${industry}`);
    if (location)
        lines.push(`**Location:** ${location}`);
    lines.push(`**Roles Found:** ${roles.length}`);
    lines.push("");
    if (roles.length === 0) {
        lines.push(`No trending roles found${industry ? ` for "${industry}"` : ""}. TrueUp may not have data for this industry or the site structure may have changed.`);
        return lines.join("\n");
    }
    // Check for error placeholders
    if (roles.length === 1 && roles[0].title.startsWith("[")) {
        lines.push("Could not retrieve trending roles data from TrueUp. The site may be temporarily unavailable or its structure may have changed.");
        lines.push("");
        lines.push("Try visiting https://www.trueup.io/trending directly for the latest data.");
        return lines.join("\n");
    }
    // Markdown table
    lines.push("| # | Role | Companies Hiring | Growth Rate | Avg Salary | Demand |");
    lines.push("|---|------|-----------------|-------------|------------|--------|");
    for (let i = 0; i < roles.length; i++) {
        const role = roles[i];
        const companies = role.companies_hiring.length > 0
            ? role.companies_hiring.slice(0, 5).join(", ") + (role.companies_hiring.length > 5 ? ` +${role.companies_hiring.length - 5} more` : "")
            : "N/A";
        const growth = role.growth_rate || "N/A";
        const salary = role.avg_salary || "N/A";
        const demand = role.demand_level || "N/A";
        // Add demand level indicator
        let demandIndicator = demand;
        if (role.demand_level === "high")
            demandIndicator = "HIGH";
        else if (role.demand_level === "medium")
            demandIndicator = "MEDIUM";
        else if (role.demand_level === "low")
            demandIndicator = "LOW";
        lines.push(`| ${i + 1} | ${role.title} | ${companies} | ${growth} | ${salary} | ${demandIndicator} |`);
    }
    lines.push("");
    // High-demand roles summary
    const highDemand = roles.filter((r) => r.demand_level === "high");
    if (highDemand.length > 0) {
        lines.push("### High-Demand Roles");
        lines.push("");
        for (const role of highDemand) {
            lines.push(`- **${role.title}**${role.avg_salary ? ` — ${role.avg_salary}` : ""}${role.growth_rate ? ` (${role.growth_rate} growth)` : ""}`);
            if (role.companies_hiring.length > 0) {
                lines.push(`  Companies: ${role.companies_hiring.join(", ")}`);
            }
        }
        lines.push("");
    }
    // Roles with salary data
    const withSalary = roles.filter((r) => r.avg_salary);
    if (withSalary.length >= 2) {
        lines.push("### Salary Comparison");
        lines.push("");
        // Sort by salary (attempt to parse)
        const sortedBySalary = [...withSalary].sort((a, b) => {
            const aNum = parseSalaryEstimate(a.avg_salary || "");
            const bNum = parseSalaryEstimate(b.avg_salary || "");
            return bNum - aNum;
        });
        lines.push("Top paying trending roles:");
        for (let i = 0; i < Math.min(5, sortedBySalary.length); i++) {
            const r = sortedBySalary[i];
            lines.push(`${i + 1}. **${r.title}** — ${r.avg_salary}`);
        }
        lines.push("");
    }
    lines.push("*Data source: TrueUp. Trending data reflects current market activity and may change frequently.*");
    // Truncate if over character limit
    let result = lines.join("\n");
    if (result.length > CHARACTER_LIMIT) {
        result = result.substring(0, CHARACTER_LIMIT - 50) + "\n\n*[Output truncated due to length]*";
    }
    return result;
}
/**
 * Best-effort parse a salary string like "$150K", "$150,000", "$120K-$180K" into a number for sorting.
 */
function parseSalaryEstimate(text) {
    if (!text)
        return 0;
    // If it's a range, take the midpoint
    const rangeMatch = text.match(/\$?([\d,]+)\s*[kK]?\s*[-–]\s*\$?([\d,]+)\s*[kK]?/);
    if (rangeMatch) {
        const low = parseAmount(rangeMatch[1]);
        const high = parseAmount(rangeMatch[2]);
        // Check for K suffix in the original text
        const hasK = text.toLowerCase().includes("k");
        const multiplier = hasK ? 1000 : 1;
        return ((low + high) / 2) * multiplier;
    }
    const singleMatch = text.match(/\$?([\d,]+)\s*([kKmM])?/);
    if (singleMatch) {
        const num = parseAmount(singleMatch[1]);
        if (singleMatch[2]?.toLowerCase() === "k")
            return num * 1000;
        if (singleMatch[2]?.toLowerCase() === "m")
            return num * 1_000_000;
        return num;
    }
    return 0;
}
function parseAmount(s) {
    return parseFloat(s.replace(/,/g, "")) || 0;
}
//# sourceMappingURL=trending-roles.js.map