import { z } from "zod";
import { interviewExperiencesSchema } from "../schemas/inputs.js";
type InterviewExperiencesInput = z.infer<typeof interviewExperiencesSchema>;
export declare function handleInterviewExperiences(input: InterviewExperiencesInput): Promise<string>;
export {};
//# sourceMappingURL=interview-experiences.d.ts.map