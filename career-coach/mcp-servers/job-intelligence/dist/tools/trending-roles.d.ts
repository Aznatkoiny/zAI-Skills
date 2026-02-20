import { z } from "zod";
import { trendingRolesSchema } from "../schemas/inputs.js";
type TrendingRolesInput = z.infer<typeof trendingRolesSchema>;
export declare function handleTrendingRoles(input: TrendingRolesInput): Promise<string>;
export {};
//# sourceMappingURL=trending-roles.d.ts.map