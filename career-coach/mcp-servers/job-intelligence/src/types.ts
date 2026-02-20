export interface JobListing {
  title: string;
  company: string;
  location: string;
  salary: string | null;
  url: string;
  description: string;
  posted_date: string | null;
  source: "indeed" | "linkedin" | "trueup";
}

export interface CompanyInfo {
  name: string;
  industry: string | null;
  size: string | null;
  rating: number | null;
  culture_ratings: Record<string, number> | null;
  interview_process: string | null;
  headquarters: string | null;
  founded: string | null;
  revenue: string | null;
}

export interface SalaryData {
  role: string;
  company: string | null;
  location: string | null;
  base: number | null;
  equity: number | null;
  bonus: number | null;
  total_comp: number | null;
  level: string | null;
  source: "glassdoor" | "levelsfyi";
}

export interface InterviewExperience {
  company: string;
  role: string | null;
  difficulty: string | null;
  experience: "positive" | "neutral" | "negative" | null;
  questions: string[];
  process: string | null;
  offer: boolean | null;
  date: string | null;
}

export interface TrendingRole {
  title: string;
  companies_hiring: string[];
  growth_rate: string | null;
  avg_salary: string | null;
  demand_level: "high" | "medium" | "low" | null;
}
