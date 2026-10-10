/**
 * job_get_interview_experiences — Glassdoor interview reviews (scraper
 * tier, cached 24h). Failures are reported honestly in the Sources footer.
 */

import { z } from "zod";
import { interviewExperiencesSchema } from "../schemas/inputs.js";
import { getGlassdoorInterviews } from "../services/glassdoor.js";
import { finalizeOutput, formatSourcesFooter } from "./sources-footer.js";

type InterviewExperiencesInput = z.infer<typeof interviewExperiencesSchema>;

export async function handleInterviewExperiences(input: InterviewExperiencesInput): Promise<string> {
  const { company_name, role } = input;

  const result = await getGlassdoorInterviews(company_name, role);
  const experiences = result.items;
  const footerLines = formatSourcesFooter([result.meta]);

  const lines: string[] = [
    `## Interview Experiences: ${company_name}`,
    "",
  ];

  if (role) lines.push(`**Role Filter:** ${role}`);
  lines.push(`**Experiences Found:** ${experiences.length}`);
  lines.push("");

  if (experiences.length === 0) {
    if (result.meta.state === "skipped") {
      lines.push("Interview experiences come from Glassdoor. This source is a website scraper, which is off by default because the site restricts automated access. Use WebSearch instead; the user can opt in by setting JOB_INTEL_ENABLE_SCRAPERS=1 (after checking the site's terms) and restarting Claude Code.");
    } else if (result.meta.state === "failed") {
      lines.push(`Could not retrieve interview data from Glassdoor: ${result.meta.detail || "unknown error"}`);
      lines.push("");
      lines.push("Fall back to WebSearch or visit Glassdoor directly for the latest interview experiences.");
    } else {
      lines.push(`No interview experiences found for "${company_name}"${role ? ` (${role})` : ""}. The company may not have interview reviews on Glassdoor.`);
    }
    return finalizeOutput(lines, footerLines);
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
    if (exp.process) {
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

  lines.push("*Data source: Glassdoor (scraper-backed, cached up to 24h). Interview experiences are self-reported and individual results may vary.*");

  return finalizeOutput(lines, footerLines);
}
