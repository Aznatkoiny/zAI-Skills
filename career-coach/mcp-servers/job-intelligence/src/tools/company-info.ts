import { z } from "zod";
import { companyInfoSchema } from "../schemas/inputs.js";
import { getGlassdoorCompanyInfo } from "../services/glassdoor.js";
import { CHARACTER_LIMIT } from "../constants.js";

type CompanyInfoInput = z.infer<typeof companyInfoSchema>;

export async function handleCompanyInfo(input: CompanyInfoInput): Promise<string> {
  const { company_name } = input;

  const info = await getGlassdoorCompanyInfo(company_name);

  const lines: string[] = [
    `## Company Profile: ${info?.name || company_name}`,
    "",
  ];

  if (!info) {
    lines.push(`No company information found for "${company_name}". The company may not be listed on Glassdoor or the search returned no results.`);
    return lines.join("\n");
  }

  // Overview section
  lines.push("### Overview");
  lines.push("");
  lines.push("| Detail | Value |");
  lines.push("|--------|-------|");
  lines.push(`| Company | ${info.name} |`);
  lines.push(`| Industry | ${info.industry || "Not available"} |`);
  lines.push(`| Size | ${info.size || "Not available"} |`);
  lines.push(`| Headquarters | ${info.headquarters || "Not available"} |`);
  lines.push(`| Founded | ${info.founded || "Not available"} |`);
  lines.push(`| Revenue | ${info.revenue || "Not available"} |`);
  lines.push("");

  // Ratings section
  lines.push("### Ratings");
  lines.push("");

  if (info.rating !== null) {
    lines.push(`**Overall Rating:** ${info.rating.toFixed(1)} / 5.0`);
    lines.push("");

    // Visual rating bar
    const filledStars = Math.round(info.rating);
    const emptyStars = 5 - filledStars;
    lines.push(`Rating: ${"*".repeat(filledStars)}${"_".repeat(emptyStars)}`);
    lines.push("");
  } else {
    lines.push("Overall rating not available.");
    lines.push("");
  }

  if (info.culture_ratings && Object.keys(info.culture_ratings).length > 0) {
    lines.push("#### Culture & Values Ratings");
    lines.push("");
    lines.push("| Category | Rating |");
    lines.push("|----------|--------|");

    for (const [category, rating] of Object.entries(info.culture_ratings)) {
      lines.push(`| ${category} | ${rating.toFixed(1)} / 5.0 |`);
    }
    lines.push("");
  }

  // Interview Process section
  lines.push("### Interview Process");
  lines.push("");

  if (info.interview_process) {
    if (info.interview_process.startsWith("Error")) {
      lines.push(`*${info.interview_process}*`);
    } else {
      lines.push(info.interview_process);
    }
  } else {
    lines.push("Interview process information not available from this source. Use the `job_get_interview_experiences` tool for detailed interview data.");
  }
  lines.push("");

  lines.push("*Data source: Glassdoor. Information may not reflect the most current state of the company.*");

  // Truncate if over character limit
  let result = lines.join("\n");
  if (result.length > CHARACTER_LIMIT) {
    result = result.substring(0, CHARACTER_LIMIT - 50) + "\n\n*[Output truncated due to length]*";
  }

  return result;
}
