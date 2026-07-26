import { z } from "zod";
import { filingTextSchema } from "../schemas/inputs.js";
import { getFilings, getFilingDocument } from "../services/edgar.js";
import { MAX_FILING_TEXT_LENGTH } from "../constants.js";

type FilingInput = z.infer<typeof filingTextSchema>;

export async function handleFilingText(input: FilingInput): Promise<string> {
  const identifier = input.ticker || input.cik;
  if (!identifier) {
    throw new Error("Either ticker or cik must be provided.");
  }

  const { company, filings } = await getFilings(identifier, input.filing_type, input.limit);

  if (filings.length === 0) {
    return `## ${company.name} (${company.ticker})\n\n*No ${input.filing_type} filings found.*`;
  }

  const lines: string[] = [
    `## ${company.name} (${company.ticker}) — ${input.filing_type} Filing(s)`,
    "",
  ];

  for (const filing of filings) {
    lines.push(`### ${filing.form} — Filed ${filing.filingDate}`);
    lines.push("");
    lines.push(`| Field | Value |`);
    lines.push(`|-------|-------|`);
    lines.push(`| Accession | ${filing.accessionNumber} |`);
    lines.push(`| Report Date | ${filing.reportDate} |`);
    lines.push(`| Document | ${filing.primaryDocDescription || filing.primaryDocument} |`);
    if (filing.items) {
      lines.push(`| Items | ${filing.items} |`);
    }
    lines.push("");

    if (filing.primaryDocument) {
      try {
        let text = await getFilingDocument(
          company.cik,
          filing.accessionNumber,
          filing.primaryDocument
        );

        const truncated = text.length > MAX_FILING_TEXT_LENGTH;
        if (truncated) {
          text = text.substring(0, MAX_FILING_TEXT_LENGTH);
        }

        lines.push("#### Filing Text");
        lines.push("");
        lines.push("```");
        lines.push(text);
        lines.push("```");

        if (truncated) {
          lines.push("");
          lines.push(`*Truncated to ${MAX_FILING_TEXT_LENGTH.toLocaleString()} characters. Full filing available at SEC EDGAR.*`);
        }
      } catch (err) {
        lines.push(`*Could not retrieve filing document: ${err instanceof Error ? err.message : "Unknown error"}*`);
      }
    } else {
      lines.push("*No primary document available for this filing.*");
    }

    lines.push("");
    lines.push("---");
    lines.push("");
  }

  lines.push(`*Data source: SEC EDGAR | ${filings.length} filing(s) retrieved*`);

  return lines.join("\n");
}
