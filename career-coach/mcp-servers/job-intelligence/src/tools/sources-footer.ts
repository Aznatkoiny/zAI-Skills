/**
 * Shared "Sources" footer rendering — every tool response ends with an
 * honest per-source status list: live / cached / skipped (no key) /
 * failed (reason). API sources and best-effort scrapers are grouped
 * separately when both are present.
 */

import { CHARACTER_LIMIT } from "../constants.js";
import type { SourceMeta } from "../types.js";

function formatAge(ageMs: number): string {
  const minutes = Math.round(ageMs / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 6) / 10;
  return `${hours}h ago`;
}

/** Render one source status line, e.g. "Remotive: live — 12 results". */
export function formatSourceLine(meta: SourceMeta): string {
  switch (meta.state) {
    case "live":
      return `- ${meta.source}: live — ${meta.count ?? 0} result${meta.count === 1 ? "" : "s"}`;
    case "cached":
      return `- ${meta.source}: cached — ${meta.count ?? 0} result${meta.count === 1 ? "" : "s"}${
        meta.ageMs !== undefined ? ` (fetched ${formatAge(meta.ageMs)})` : ""
      }`;
    case "stale-cache":
      return `- ${meta.source}: cached (stale) — ${meta.count ?? 0} result${meta.count === 1 ? "" : "s"}${
        meta.ageMs !== undefined ? ` from ${formatAge(meta.ageMs)}` : ""
      }; live fetch failed`;
    case "skipped":
      return `- ${meta.source}: skipped (${meta.detail || "disabled"})`;
    case "failed":
      return `- ${meta.source}: failed (${meta.detail || "unknown error"})`;
  }
}

/** Render the full "Sources" footer section for a list of source metas. */
export function formatSourcesFooter(metas: SourceMeta[]): string[] {
  const lines: string[] = ["### Sources", ""];

  const api = metas.filter((m) => m.tier === "api");
  const scrapers = metas.filter((m) => m.tier === "scraper");

  if (api.length > 0 && scrapers.length > 0) {
    lines.push("**APIs (primary):**");
    lines.push(...api.map(formatSourceLine));
    lines.push("");
    lines.push("**Scrapers (best-effort):**");
    lines.push(...scrapers.map(formatSourceLine));
  } else {
    lines.push(...metas.map(formatSourceLine));
  }

  return lines;
}

/**
 * Join body + footer, truncating the body if needed so the Sources footer
 * always survives the CHARACTER_LIMIT.
 */
export function finalizeOutput(bodyLines: string[], footerLines: string[]): string {
  const footer = footerLines.join("\n");
  let body = bodyLines.join("\n");

  const budget = CHARACTER_LIMIT - footer.length - 60;
  if (body.length > budget) {
    body = body.substring(0, Math.max(0, budget)) + "\n\n*[Output truncated due to length]*";
  }

  return `${body}\n\n${footer}`;
}
