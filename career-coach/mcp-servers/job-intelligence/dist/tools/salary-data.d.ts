import { z } from "zod";
import { salaryDataSchema } from "../schemas/inputs.js";
type SalaryDataInput = z.infer<typeof salaryDataSchema>;
export declare function handleSalaryData(input: SalaryDataInput): Promise<string>;
export {};
//# sourceMappingURL=salary-data.d.ts.map