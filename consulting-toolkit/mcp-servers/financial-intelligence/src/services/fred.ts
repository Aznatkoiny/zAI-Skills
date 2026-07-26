import axios, { type AxiosInstance } from "axios";
import { FRED_BASE_URL, RATE_LIMITS } from "../constants.js";
import type { FredSeriesInfo, FredObservation, MacroIndicatorData } from "../types.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.fred);

function getApiKey(): string {
  const key = process.env.FRED_API_KEY;
  if (!key) {
    throw new Error(
      "FRED_API_KEY environment variable is required. Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html"
    );
  }
  return key;
}

function createClient(): AxiosInstance {
  return axios.create({
    baseURL: FRED_BASE_URL,
    timeout: 15_000,
  });
}

let client: AxiosInstance | null = null;
function getClient(): AxiosInstance {
  if (!client) client = createClient();
  return client;
}

export async function getSeriesInfo(seriesId: string): Promise<FredSeriesInfo> {
  const apiKey = getApiKey();
  await limiter.acquire();
  const { data } = await getClient().get("/series", {
    params: {
      series_id: seriesId,
      api_key: apiKey,
      file_type: "json",
    },
  });

  const s = data.seriess?.[0];
  if (!s) {
    throw new Error(`FRED series "${seriesId}" not found.`);
  }

  return {
    id: s.id,
    title: s.title,
    units: s.units,
    frequency: s.frequency,
    seasonalAdjustment: s.seasonal_adjustment,
    lastUpdated: s.last_updated,
    notes: s.notes || "",
  };
}

export async function getObservations(
  seriesId: string,
  startDate?: string,
  endDate?: string,
  limit: number = 20
): Promise<MacroIndicatorData> {
  const apiKey = getApiKey();
  const series = await getSeriesInfo(seriesId);

  await limiter.acquire();
  const params: Record<string, string | number> = {
    series_id: seriesId,
    api_key: apiKey,
    file_type: "json",
    sort_order: "desc",
    limit,
  };
  if (startDate) params.observation_start = startDate;
  if (endDate) params.observation_end = endDate;

  const { data } = await getClient().get("/series/observations", { params });

  const observations: FredObservation[] = (data.observations || []).map(
    (obs: { date: string; value: string }) => ({
      date: obs.date,
      value: obs.value === "." ? null : parseFloat(obs.value),
    })
  );

  return { series, observations };
}
