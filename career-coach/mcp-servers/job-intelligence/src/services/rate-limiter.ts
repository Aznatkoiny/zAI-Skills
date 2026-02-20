export class RateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly maxTokens: number;
  private readonly refillRate: number; // tokens per second

  constructor(requestsPerSecond: number) {
    this.maxTokens = requestsPerSecond;
    this.refillRate = requestsPerSecond;
    this.tokens = requestsPerSecond;
    this.lastRefill = Date.now();
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens >= 1) {
      this.tokens -= 1;
      return;
    }
    // Wait until a token is available
    const waitMs = ((1 - this.tokens) / this.refillRate) * 1000;
    await new Promise((resolve) => setTimeout(resolve, Math.ceil(waitMs)));
    this.refill();
    this.tokens -= 1;
  }
}
