import { z } from "zod";
import { companyInfoSchema } from "../schemas/inputs.js";
type CompanyInfoInput = z.infer<typeof companyInfoSchema>;
export declare function handleCompanyInfo(input: CompanyInfoInput): Promise<string>;
export {};
//# sourceMappingURL=company-info.d.ts.map