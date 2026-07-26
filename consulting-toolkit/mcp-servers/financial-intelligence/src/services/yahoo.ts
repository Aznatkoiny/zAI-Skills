import axios from "axios";
import { RATE_LIMITS } from "../constants.js";
import type { StockQuote, StockPricePoint, StockData } from "../types.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.yahoo);

const YAHOO_CHART_BASE = "https://query1.finance.yahoo.com/v8/finance/chart";

const PERIOD_MAP: Record<string, string> = {
  "1d": "1d",
  "5d": "5d",
  "1mo": "1mo",
  "3mo": "3mo",
  "6mo": "6mo",
  "1y": "1y",
  "2y": "2y",
  "5y": "5y",
  max: "max",
};

const INTERVAL_MAP: Record<string, string> = {
  "1d": "1d",
  "1wk": "1wk",
  "1mo": "1mo",
};

interface YahooChartMeta {
  symbol?: string;
  shortName?: string;
  longName?: string;
  regularMarketPrice?: number;
  previousClose?: number;
  regularMarketPreviousClose?: number;
  fiftyTwoWeekHigh?: number;
  fiftyTwoWeekLow?: number;
}

interface YahooChartIndicatorQuote {
  open: (number | null)[];
  high: (number | null)[];
  low: (number | null)[];
  close: (number | null)[];
  volume: (number | null)[];
}

interface YahooChartResult {
  meta?: YahooChartMeta;
  timestamp?: number[];
  indicators?: {
    quote?: YahooChartIndicatorQuote[];
  };
}

export async function getStockData(
  ticker: string,
  period: string = "1y",
  interval: string = "1d"
): Promise<StockData> {
  const mappedPeriod = PERIOD_MAP[period] || "1y";
  const mappedInterval = INTERVAL_MAP[interval] || "1d";

  // Use v8 chart endpoint — returns both meta (quote-like data) and historical prices
  await limiter.acquire();
  const chartResp = await axios.get(
    `${YAHOO_CHART_BASE}/${ticker.toUpperCase()}`,
    {
      params: { range: mappedPeriod, interval: mappedInterval },
      headers: { "User-Agent": "Mozilla/5.0" },
      timeout: 15_000,
    }
  );

  const chartResult: YahooChartResult =
    chartResp.data?.chart?.result?.[0] || {};
  const meta = chartResult.meta || {};
  const timestamps = chartResult.timestamp || [];
  const quotes = chartResult.indicators?.quote?.[0];

  const currentPrice = meta.regularMarketPrice || 0;

  const history: StockPricePoint[] = [];
  if (quotes) {
    for (let i = 0; i < timestamps.length; i++) {
      const close = quotes.close[i];
      if (close == null) continue;
      history.push({
        date: new Date(timestamps[i] * 1000).toISOString().split("T")[0],
        open: quotes.open[i] || 0,
        high: quotes.high[i] || 0,
        low: quotes.low[i] || 0,
        close,
        volume: quotes.volume[i] || 0,
      });
    }
  }

  // Previous close: chart meta only carries it for short ranges, so fall back
  // to the prior daily bar; report null (rendered N/A) when unavailable.
  let prevClose: number | null =
    meta.previousClose ?? meta.regularMarketPreviousClose ?? null;
  if (!prevClose && mappedInterval === "1d" && history.length >= 2) {
    prevClose = history[history.length - 2].close;
  }
  const change = prevClose ? currentPrice - prevClose : null;
  const changePercent = prevClose ? ((currentPrice - prevClose) / prevClose) * 100 : null;

  const stockQuote: StockQuote = {
    ticker: ticker.toUpperCase(),
    name: meta.shortName || meta.longName || ticker,
    price: currentPrice,
    change,
    changePercent,
    fiftyTwoWeekHigh: meta.fiftyTwoWeekHigh || 0,
    fiftyTwoWeekLow: meta.fiftyTwoWeekLow || 0,
    avgVolume: 0,
    avgVolumeBars: 0,
  };

  // Compute avg volume over the most recent bars (up to 60) of the returned history
  if (history.length > 0) {
    const recentVols = history.slice(-60);
    stockQuote.avgVolume = Math.round(
      recentVols.reduce((sum, h) => sum + h.volume, 0) / recentVols.length
    );
    stockQuote.avgVolumeBars = recentVols.length;
  }

  return {
    quote: stockQuote,
    history,
    period: mappedPeriod,
    interval: mappedInterval,
  };
}
