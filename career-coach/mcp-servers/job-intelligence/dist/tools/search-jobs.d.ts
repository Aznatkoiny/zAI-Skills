import { z } from "zod";
import { searchJobsSchema } from "../schemas/inputs.js";
type SearchJobsInput = z.infer<typeof searchJobsSchema>;
export declare function handleSearchJobs(input: SearchJobsInput): Promise<string>;
export {};
//# sourceMappingURL=search-jobs.d.ts.map