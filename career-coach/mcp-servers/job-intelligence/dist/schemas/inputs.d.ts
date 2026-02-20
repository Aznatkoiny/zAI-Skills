import { z } from "zod";
export declare const searchJobsSchema: z.ZodObject<{
    query: z.ZodString;
    location: z.ZodOptional<z.ZodString>;
    remote: z.ZodDefault<z.ZodOptional<z.ZodBoolean>>;
    salary_min: z.ZodOptional<z.ZodNumber>;
    experience_level: z.ZodOptional<z.ZodEnum<["entry", "mid", "senior", "lead", "executive"]>>;
    limit: z.ZodDefault<z.ZodOptional<z.ZodNumber>>;
}, "strip", z.ZodTypeAny, {
    query: string;
    remote: boolean;
    limit: number;
    location?: string | undefined;
    salary_min?: number | undefined;
    experience_level?: "entry" | "mid" | "senior" | "lead" | "executive" | undefined;
}, {
    query: string;
    location?: string | undefined;
    remote?: boolean | undefined;
    salary_min?: number | undefined;
    experience_level?: "entry" | "mid" | "senior" | "lead" | "executive" | undefined;
    limit?: number | undefined;
}>;
export declare const companyInfoSchema: z.ZodObject<{
    company_name: z.ZodString;
}, "strip", z.ZodTypeAny, {
    company_name: string;
}, {
    company_name: string;
}>;
export declare const salaryDataSchema: z.ZodObject<{
    role: z.ZodString;
    company: z.ZodOptional<z.ZodString>;
    location: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    role: string;
    location?: string | undefined;
    company?: string | undefined;
}, {
    role: string;
    location?: string | undefined;
    company?: string | undefined;
}>;
export declare const interviewExperiencesSchema: z.ZodObject<{
    company_name: z.ZodString;
    role: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    company_name: string;
    role?: string | undefined;
}, {
    company_name: string;
    role?: string | undefined;
}>;
export declare const trendingRolesSchema: z.ZodObject<{
    industry: z.ZodOptional<z.ZodString>;
    location: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    location?: string | undefined;
    industry?: string | undefined;
}, {
    location?: string | undefined;
    industry?: string | undefined;
}>;
//# sourceMappingURL=inputs.d.ts.map