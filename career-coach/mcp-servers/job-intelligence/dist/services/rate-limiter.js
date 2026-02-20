export class RateLimiter {
    tokens;
    lastRefill;
    maxTokens;
    refillRate; // tokens per second
    constructor(requestsPerSecond) {
        this.maxTokens = requestsPerSecond;
        this.refillRate = requestsPerSecond;
        this.tokens = requestsPerSecond;
        this.lastRefill = Date.now();
    }
    refill() {
        const now = Date.now();
        const elapsed = (now - this.lastRefill) / 1000;
        this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
        this.lastRefill = now;
    }
    async acquire() {
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
//# sourceMappingURL=rate-limiter.js.map