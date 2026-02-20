export declare class RateLimiter {
    private tokens;
    private lastRefill;
    private readonly maxTokens;
    private readonly refillRate;
    constructor(requestsPerSecond: number);
    private refill;
    acquire(): Promise<void>;
}
//# sourceMappingURL=rate-limiter.d.ts.map