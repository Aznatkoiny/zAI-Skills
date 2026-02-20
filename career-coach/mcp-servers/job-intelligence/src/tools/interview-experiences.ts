import { z } from "zod";
import { interviewExperiencesSchema } from "../schemas/inputs.js";
import { getGlassdoorInterviews } from "../services/glassdoor.js";
import { CHARACTER_LIMIT } from "../constants.js";

type InterviewExperiencesInput = z.infer<typeof interviewExperiencesSchema>;

export async function handleInterviewExperiences(input: InterviewExperiencesInput): Promise<string> {
  const { company_name, role } = input;

  const experiences = await getGlassdoorInterviews(company_name, role);

  const lines: string[] = [
    `## Interview Experiences: ${company_name}`,
    "",
  ];

  if (role) lines.push(`**Role Filter:** ${role}`);
  lines.push(`**Experiences Found:** ${experiences.length}`);
  lines.push("");

  if (experiences.length === 0) {
    lines.push(`No interview experiences found for "${company_name}"${role ? ` (${role})` : ""}. The company may not have interview reviews on Glassdoor.`);
    return lines.join("\n");
  }

  // Check if we only have error placeholders
  const hasRealData = experiences.some((e) => e.difficulty || e.experience || e.questions.length > 0 || (e.process && !e.process.startsWith("Error")));

  if (!hasRealData && experiences.length === 1 && experiences[0].process?.startsWith("Error")) {
    lines.push(`Could not retrieve interview data: ${experiences[0].process}`);
    lines.push("");
    lines.push("Try searching on Glassdoor directly for the latest interview experiences.");
    return lines.join("\n");
  }

  // Summary statistics
  const difficulties = experiences.map((e) => e.difficulty).filter(Boolean);
  const sentiments = experiences.map((e) => e.experience).filter(Boolean);
  const offers = experiences.map((e) => e.offer).filter((o): o is boolean => o !== null);

  if (sentiments.length > 0 || offers.length > 0) {
    lines.push("### Summary");
    lines.push("");

    if (sentiments.length > 0) {
      const positive = sentiments.filter((s) => s === "positive").length;
      const neutral = sentiments.filter((s) => s === "neutral").length;
      const negative = sentiments.filter((s) => s === "negative").length;
      lines.push(`**Sentiment:** ${positive} positive, ${neutral} neutral, ${negative} negative`);
    }

    if (difficulties.length > 0) {
      lines.push(`**Difficulty Levels:** ${difficulties.join(", ")}`);
    }

    if (offers.length > 0) {
      const offerCount = offers.filter((o) => o).length;
      const offerRate = ((offerCount / offers.length) * 100).toFixed(0);
      lines.push(`**Offer Rate:** ${offerCount}/${offers.length} (${offerRate}%)`);
    }

    lines.push("");
  }

  // Individual experiences
  lines.push("### Individual Experiences");
  lines.push("");

  for (let i = 0; i < experiences.length; i++) {
    const exp = experiences[i];

    lines.push(`---`);
    lines.push(`#### Experience ${i + 1}${exp.role ? ` — ${exp.role}` : ""}`);
    lines.push("");

    // Metadata row
    const meta: string[] = [];
    if (exp.difficulty) meta.push(`**Difficulty:** ${exp.difficulty}`);
    if (exp.experience) meta.push(`**Outcome:** ${exp.experience}`);
    if (exp.offer !== null) meta.push(`**Offer:** ${exp.offer ? "Yes" : "No"}`);
    if (exp.date) meta.push(`**Date:** ${exp.date}`);

    if (meta.length > 0) {
      lines.push(meta.join(" | "));
      lines.push("");
    }

    // Process description
    if (exp.process && !exp.process.startsWith("Error")) {
      lines.push("**Interview Process:**");
      lines.push(`> ${exp.process}`);
      lines.push("");
    }

    // Questions
    if (exp.questions.length > 0) {
      lines.push("**Questions Asked:**");
      for (const q of exp.questions) {
        lines.push(`- ${q}`);
      }
      lines.push("");
    }
  }

  lines.push("*Data source: Glassdoor. Interview experiences are self-reported and individual results may vary.*");

  // Truncate if over character limit
  let result = lines.join("\n");
  if (result.length > CHARACTER_LIMIT) {
    result = result.substring(0, CHARACTER_LIMIT - 50) + "\n\n*[Output truncated due to length]*";
  }

  return result;
}
