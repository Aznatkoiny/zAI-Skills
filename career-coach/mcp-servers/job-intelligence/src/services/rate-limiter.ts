/**
 * FIFO promise-queue rate limiter.
 *
 * Each acquire() synchronously reserves the next available time slot
 * (spaced 1/requestsPerSecond apart) before awaiting, so concurrent
 * callers get distinct slots in call order and the rate is actually
 * enforced. An idle limiter always allows the first request immediately,
 * including for fractional rates (e.g. 0.2 req/s).
 */
export class RateLimiter {
  private readonly intervalMs: number;
  private lastScheduled = 0;

  constructor(requestsPerSecond: number) {
    if (requestsPerSecond <= 0) {
      throw new Error(`requestsPerSecond must be positive, got ${requestsPerSecond}`);
    }
    this.intervalMs = 1000 / requestsPerSecond;
  }

  async acquire(): Promise<void> {
    const now = Date.now();
    const next = Math.max(now, this.lastScheduled + this.intervalMs);
    this.lastScheduled = next;

    const waitMs = next - now;
    if (waitMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, waitMs));
    }
  }
}
