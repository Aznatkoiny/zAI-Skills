/**
 * FIFO promise-queue rate limiter.
 *
 * Each acquire() synchronously reserves the next free slot on a shared
 * timeline — slots are spaced 1000/requestsPerSecond ms apart — and then
 * sleeps until its slot arrives. Because the reservation happens before any
 * await, concurrent callers are serialized in call order and the configured
 * rate is enforced even under concurrency (a naive token bucket lets all
 * concurrent acquirers observe the same token count and proceed together).
 *
 * An idle limiter always grants the first request immediately: lastScheduled
 * lies in the past, so the next slot is "now". This also fixes fractional
 * rates (e.g. 0.1 req/s), where a token bucket capped at maxTokens < 1 could
 * never hold a full token and made even the first request wait.
 */
export class RateLimiter {
  private readonly intervalMs: number;
  private lastScheduled = 0;

  constructor(requestsPerSecond: number) {
    if (!Number.isFinite(requestsPerSecond) || requestsPerSecond <= 0) {
      throw new Error(`requestsPerSecond must be a positive number, got ${requestsPerSecond}`);
    }
    this.intervalMs = 1000 / requestsPerSecond;
  }

  async acquire(): Promise<void> {
    const now = Date.now();
    const next = Math.max(now, this.lastScheduled + this.intervalMs);
    this.lastScheduled = next;
    if (next > now) {
      await new Promise<void>((resolve) => setTimeout(resolve, next - now));
    }
  }
}
