import type { CompanyInfo, SalaryData, InterviewExperience } from "../types.js";
/**
 * Search for a company on Glassdoor and retrieve company overview information.
 */
export declare function getGlassdoorCompanyInfo(company: string): Promise<CompanyInfo | null>;
/**
 * Get salary data for a specific role from Glassdoor.
 */
export declare function getGlassdoorSalaries(role: string, company?: string): Promise<SalaryData[]>;
/**
 * Get interview experiences from Glassdoor for a specific company.
 */
export declare function getGlassdoorInterviews(company: string, role?: string): Promise<InterviewExperience[]>;
//# sourceMappingURL=glassdoor.d.ts.map