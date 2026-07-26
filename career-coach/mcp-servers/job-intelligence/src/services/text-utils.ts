/** Small text helpers shared by the API services. */

/** Strip HTML tags/entities from an API-provided description into plain text. */
export function stripHtml(html: string): string {
  return html
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&quot;/gi, '"')
    .replace(/\s+/g, " ")
    .trim();
}

/** Truncate to maxLen characters, appending an ellipsis when cut. */
export function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen).trimEnd() + "...";
}

/** Format a dollar range like "$120,000 - $180,000" from optional bounds. */
export function formatSalaryRange(min?: number | null, max?: number | null): string | null {
  const lo = typeof min === "number" && min > 0 ? min : null;
  const hi = typeof max === "number" && max > 0 ? max : null;
  if (lo !== null && hi !== null && hi !== lo) {
    return `$${Math.round(lo).toLocaleString()} - $${Math.round(hi).toLocaleString()}`;
  }
  const single = hi ?? lo;
  return single !== null ? `$${Math.round(single).toLocaleString()}` : null;
}
