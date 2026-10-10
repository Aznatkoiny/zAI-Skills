import { z } from "zod";
import { earningsTranscriptSchema } from "../schemas/inputs.js";
import { findExhibitDocument, getFilings, getFilingDocument } from "../services/edgar.js";
import { MAX_FILING_TEXT_LENGTH } from "../constants.js";

type EarningsInput = z.infer<typeof earningsTranscriptSchema>;

export async function handleEarningsTranscript(input: EarningsInput): Promise<string> {
  const identifier = input.ticker || input.cik;
  if (!identifier) {
    throw new Error("Either ticker or cik must be provided.");
  }

  // Fetch more 8-K filings than requested so we can filter for earnings-related ones
  const { company, filings } = await getFilings(identifier, "8-K", input.limit * 5);

  // Filter for earnings-related 8-K filings (Item 2.02 — Results of Operations and Financial Condition)
  const earningsFilings = filings.filter((f) => {
    const items = f.items.toLowerCase();
    return items.includes("2.02") || items.includes("item 2.02");
  });

  const targetFilings = earningsFilings.slice(0, input.limit);

  const lines: string[] = [
    `## ${company.name} (${company.ticker}) — Earnings Releases (8-K Item 2.02)`,
    "",
  ];

  if (targetFilings.length === 0) {
    lines.push("*No earnings-related 8-K filings (Item 2.02) found.*");
    lines.push("");
    lines.push("**Note:** True earnings call transcripts are not available via free public APIs. ");
    lines.push("SEC 8-K filings with Item 2.02 (Results of Operations and Financial Condition) ");
    lines.push("are the closest publicly available proxy, typically containing the press release ");
    lines.push("announcing quarterly results.");

    // Show available 8-K filings as fallback
    if (filings.length > 0) {
      lines.push("");
      lines.push("### Available 8-K Filings");
      lines.push("");
      lines.push("| Date | Items | Description |");
      lines.push("|------|-------|-------------|");
      for (const f of filings.slice(0, 5)) {
        lines.push(`| ${f.filingDate} | ${f.items || "N/A"} | ${f.primaryDocDescription || "—"} |`);
      }
    }
  } else {
    for (const filing of targetFilings) {
      lines.push(`### Earnings Release — Filed ${filing.filingDate}`);
      lines.push("");
      lines.push(`| Field | Value |`);
      lines.push(`|-------|-------|`);
      lines.push(`| Accession | ${filing.accessionNumber} |`);
      lines.push(`| Report Date | ${filing.reportDate} |`);
      lines.push(`| Items | ${filing.items} |`);
      lines.push("");

      if (filing.primaryDocument) {
        try {
          // The 8-K itself is a short cover form; the results and management's
          // commentary are in the press release, filed as Exhibit 99.1.
          const exhibit = await findExhibitDocument(company.cik, filing.accessionNumber);
          const document = exhibit ?? filing.primaryDocument;
          lines.push(
            exhibit
              ? `*Source document: Exhibit 99.1 press release (${exhibit})*`
              : `*Source document: 8-K form (${filing.primaryDocument}); no Exhibit 99.1 was found, so the results may be in another exhibit*`
          );
          lines.push("");
          let text = await getFilingDocument(company.cik, filing.accessionNumber, document);

          const truncated = text.length > MAX_FILING_TEXT_LENGTH;
          if (truncated) {
            text = text.substring(0, MAX_FILING_TEXT_LENGTH);
          }

          lines.push("#### Press release text");
          lines.push("");
          lines.push("```");
          lines.push(text);
          lines.push("```");

          if (truncated) {
            lines.push("");
            lines.push(`*Truncated to ${MAX_FILING_TEXT_LENGTH.toLocaleString()} characters.*`);
          }
        } catch (err) {
          lines.push(`*Could not retrieve document: ${err instanceof Error ? err.message : "Unknown error"}*`);
        }
      }

      lines.push("");
      lines.push("---");
      lines.push("");
    }
  }

  lines.push("");
  lines.push("*Data source: SEC EDGAR 8-K filings (Item 2.02), Exhibit 99.1 press releases.*");
  lines.push("*This is the company's written earnings release, not a transcript of the earnings call. Don't attribute quotes to the call unless they appear here; call transcripts require a paid data provider.*");

  return lines.join("\n");
}
