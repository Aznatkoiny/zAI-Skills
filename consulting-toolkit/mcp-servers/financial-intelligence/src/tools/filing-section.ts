import { z } from "zod";
import { filingSectionSchema } from "../schemas/inputs.js";
import { getFilings, getFilingDocument } from "../services/edgar.js";
import { extractSection, isSectionAvailable } from "../services/filing-sections.js";
import { FILING_SECTION_PAGE_SIZE } from "../constants.js";

type FilingSectionInput = z.infer<typeof filingSectionSchema>;

export async function handleFilingSection(input: FilingSectionInput): Promise<string> {
  const identifier = input.ticker || input.cik;
  if (!identifier) {
    throw new Error("Either ticker or cik must be provided.");
  }

  if (!isSectionAvailable(input.section, input.filing_type)) {
    throw new Error(
      `Section "${input.section}" is not part of a ${input.filing_type}. ` +
        `The Business section (Item 1) only appears in 10-K filings — retry with filing_type "10-K".`
    );
  }

  const { company, filings } = await getFilings(identifier, input.filing_type, 1);

  if (filings.length === 0) {
    return `## ${company.name} (${company.ticker})\n\n*No ${input.filing_type} filings found.*`;
  }

  const filing = filings[0];
  const header = [
    `## ${company.name} (${company.ticker}) — ${filing.form} filed ${filing.filingDate}`,
    "",
  ];

  if (!filing.primaryDocument) {
    return [...header, `*Filing ${filing.accessionNumber} has no primary document to extract from.*`].join("\n");
  }

  const text = await getFilingDocument(company.cik, filing.accessionNumber, filing.primaryDocument);
  const located = extractSection(text, input.section, input.filing_type);

  if (!located) {
    return [
      ...header,
      `*Could not locate the "${input.section}" section boundaries in this filing's primary document ` +
        `(${filing.primaryDocument}). The filing may use nonstandard item headings. ` +
        `Fall back to fin_get_filing_text for the raw document, or read the filing on EDGAR ` +
        `(accession ${filing.accessionNumber}).*`,
    ].join("\n");
  }

  const totalPages = Math.max(1, Math.ceil(located.text.length / FILING_SECTION_PAGE_SIZE));
  if (input.page > totalPages) {
    return [
      ...header,
      `*${located.label} has ${totalPages} page(s) (${located.text.length.toLocaleString()} characters); ` +
        `page ${input.page} does not exist. Request a page between 1 and ${totalPages}.*`,
    ].join("\n");
  }

  const startChar = (input.page - 1) * FILING_SECTION_PAGE_SIZE;
  const slice = located.text.slice(startChar, startChar + FILING_SECTION_PAGE_SIZE);
  const endChar = startChar + slice.length;

  const lines: string[] = [
    `## ${company.name} (${company.ticker}) — ${located.label}`,
    "",
    `| Field | Value |`,
    `|-------|-------|`,
    `| Filing | ${filing.form} filed ${filing.filingDate} (period ${filing.reportDate}) |`,
    `| Accession | ${filing.accessionNumber} |`,
    `| Section length | ${located.text.length.toLocaleString()} characters |`,
    "",
  ];

  if (located.approximate) {
    lines.push(
      "*Note: section boundaries were located by fallback item-number matching (standard headings were not found); verify the start and end of this text against the source filing.*",
      ""
    );
  }

  lines.push("```", slice, "```", "");

  if (totalPages > 1) {
    const next =
      input.page < totalPages
        ? `Call fin_get_filing_section again with page: ${input.page + 1} to continue.`
        : "End of section.";
    lines.push(
      `--- Page ${input.page} of ${totalPages} — characters ${(startChar + 1).toLocaleString()}–${endChar.toLocaleString()} of ${located.text.length.toLocaleString()}. ${next} ---`
    );
  } else {
    lines.push(`--- Complete section (${located.text.length.toLocaleString()} characters, 1 page). ---`);
  }

  lines.push(
    "",
    "*Data source: SEC EDGAR filing text; section boundaries located heuristically from item headings.*"
  );

  return lines.join("\n");
}
