# Server-Side Implementation Patterns

## Table of Contents

1. [Express Middleware](#express-middleware)
2. [Next.js Middleware](#nextjs-middleware)
3. [Hono Middleware](#hono-middleware)
4. [Multi-Route Configuration](#multi-route-configuration)
5. [Multi-Chain Server (EVM + Solana)](#multi-chain-server)
6. [Dynamic Pricing (Without Middleware)](#dynamic-pricing)
7. [Delayed Settlement](#delayed-settlement)
8. [Facilitator Configuration](#facilitator-configuration)
9. [Bazaar Discovery Extension](#bazaar-discovery)
10. [Environment Variables Template](#env-template)

## Express Middleware

Source: `examples/typescript/servers/express/`

```typescript
import express from "express";
import { paymentMiddleware } from "@x402/express";
import { x402ResourceServer, HTTPFacilitatorClient } from "@x402/core/server";
import { registerExactEvmScheme } from "@x402/evm/exact/server";

const app = express();
const payTo = process.env.PAY_TO!;

const facilitatorClient = new HTTPFacilitatorClient({
  url: "https://x402.org/facilitator",
});
const server = new x402ResourceServer(facilitatorClient);
registerExactEvmScheme(server);

app.use(
  paymentMiddleware(
    {
      "GET /weather": {
        accepts: [
          { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo },
        ],
        description: "Get current weather data",
        mimeType: "application/json",
      },
    },
    server,
  ),
);

app.get("/weather", (req, res) => {
  res.json({ report: { weather: "sunny", temperature: 70 } });
});

app.listen(4021);
```

**Alternative registration style** (from CDP docs — equivalent):
```typescript
import { paymentMiddleware, x402ResourceServer } from "@x402/express";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { HTTPFacilitatorClient } from "@x402/core/server";

const server = new x402ResourceServer(facilitatorClient)
  .register("eip155:84532", new ExactEvmScheme());
```

## Next.js Middleware

Source: `examples/typescript/fullstack/mainnet/`

```typescript
// middleware.ts
import { paymentProxy } from "@x402/next";
import { x402ResourceServer, HTTPFacilitatorClient } from "@x402/core/server";
import { registerExactEvmScheme } from "@x402/evm/exact/server";

const payTo = process.env.PAY_TO!;
const facilitatorClient = new HTTPFacilitatorClient({
  url: "https://x402.org/facilitator",
});
const server = new x402ResourceServer(facilitatorClient);
registerExactEvmScheme(server);

export const middleware = paymentProxy(
  {
    "/api/protected": {
      accepts: [
        { scheme: "exact", price: "$0.01", network: "eip155:84532", payTo },
      ],
      description: "Access to protected content",
      mimeType: "application/json",
    },
  },
  server,
);

export const config = {
  matcher: ["/api/protected/:path*"],
};
```

## Hono Middleware

```typescript
import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { paymentMiddleware } from "@x402/hono";
import { x402ResourceServer, HTTPFacilitatorClient } from "@x402/core/server";
import { registerExactEvmScheme } from "@x402/evm/exact/server";

const app = new Hono();
const payTo = process.env.PAY_TO!;

const facilitatorClient = new HTTPFacilitatorClient({
  url: "https://x402.org/facilitator",
});
const server = new x402ResourceServer(facilitatorClient);
registerExactEvmScheme(server);

app.use(
  paymentMiddleware(
    {
      "/data": {
        accepts: [
          { scheme: "exact", price: "$0.10", network: "eip155:84532", payTo },
        ],
        description: "Premium data endpoint",
      },
    },
    server,
  ),
);

app.get("/data", (c) => c.json({ message: "Premium content" }));
serve({ fetch: app.fetch, port: 3000 });
```

## Multi-Route Configuration

Route keys use `"METHOD /path"` format. Supports wildcards.

```typescript
app.use(
  paymentMiddleware(
    {
      "GET /free": null, // Explicitly no payment
      "GET /cheap": {
        accepts: [
          { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo },
        ],
      },
      "GET /premium": {
        accepts: [
          { scheme: "exact", price: "$0.10", network: "eip155:84532", payTo },
        ],
      },
      "POST /api/*": {
        accepts: [
          { scheme: "exact", price: "$0.01", network: "eip155:84532", payTo },
        ],
      },
    },
    server,
  ),
);
```

## Multi-Chain Server

Source: Accept payments on both EVM and Solana.

```typescript
import { registerExactEvmScheme } from "@x402/evm/exact/server";
import { registerExactSvmScheme } from "@x402/svm/exact/server";

const server = new x402ResourceServer(facilitatorClient);
registerExactEvmScheme(server);
registerExactSvmScheme(server);

app.use(
  paymentMiddleware(
    {
      "GET /multi": {
        accepts: [
          { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo: evmAddress },
          {
            scheme: "exact",
            price: "$0.001",
            network: "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1",
            payTo: solanaAddress,
          },
        ],
      },
    },
    server,
  ),
);
```

## Dynamic Pricing

Source: `examples/typescript/servers/advanced/`

Handle pricing without middleware for full control over verify/settle flow.

```typescript
app.get("/dynamic-price", async (req, res) => {
  const multiplier = parseInt(req.query.multiplier as string) || 1;
  const basePrice = 0.001;
  const price = `$${(basePrice * multiplier).toFixed(6)}`;

  const paymentConfig = {
    accepts: [{ scheme: "exact", price, network: "eip155:84532", payTo }],
    description: "Dynamic pricing endpoint",
  };

  const paymentHeader = req.headers["payment-signature"] as string;

  if (!paymentHeader) {
    res.status(402).set(
      "PAYMENT-REQUIRED",
      Buffer.from(JSON.stringify({ x402Version: 2, ...paymentConfig })).toString("base64"),
    );
    return res.json({ error: "Payment required" });
  }

  const verifyResult = await server.verify(paymentHeader, paymentConfig);
  if (!verifyResult.isValid) {
    return res.status(402).json({ error: verifyResult.invalidReason });
  }

  // Perform work BEFORE settling (delayed settlement pattern)
  const result = await expensiveOperation(multiplier);

  const settleResult = await server.settle(paymentHeader, paymentConfig);
  res.set("PAYMENT-RESPONSE", settleResult.encoded);
  res.json({ result, txHash: settleResult.txHash });
});
```

## Delayed Settlement

Source: `examples/typescript/servers/advanced/`

Verify first, do work, then settle. Useful when immediate response matters more than payment guarantee.

```typescript
app.get("/delayed", async (req, res) => {
  const paymentHeader = req.headers["payment-signature"] as string;
  if (!paymentHeader) { /* return 402 */ }

  // Step 1: Verify only
  const verifyResult = await server.verify(paymentHeader, paymentConfig);
  if (!verifyResult.isValid) { /* return 402 */ }

  // Step 2: Do expensive work
  const result = await generateContent();

  // Step 3: Settle after work completes
  const settleResult = await server.settle(paymentHeader, paymentConfig);

  res.set("PAYMENT-RESPONSE", settleResult.encoded);
  res.json(result);
});
```

## Facilitator Configuration

```typescript
// Testnet (no auth, free)
const testnetFacilitator = new HTTPFacilitatorClient({
  url: "https://x402.org/facilitator",
});

// Mainnet via CDP (requires API keys)
const mainnetFacilitator = new HTTPFacilitatorClient({
  url: "https://api.cdp.coinbase.com/platform/v2/x402",
  createAuthHeaders: () => ({
    Authorization: `Bearer ${process.env.CDP_API_KEY}`,
  }),
});

// Environment-based selection
const facilitatorClient = new HTTPFacilitatorClient({
  url:
    process.env.NODE_ENV === "production"
      ? "https://api.cdp.coinbase.com/platform/v2/x402"
      : "https://x402.org/facilitator",
});
```

## Bazaar Discovery

Expose endpoints for automated discovery by agents and facilitators.

```typescript
app.use(
  paymentMiddleware(
    {
      "GET /weather": {
        accepts: [
          { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo },
        ],
        description: "Real-time weather data for any city",
        mimeType: "application/json",
        extensions: {
          bazaar: {
            discoverable: true,
            category: "weather",
            tags: ["forecast", "real-time"],
          },
        },
      },
    },
    server,
  ),
);
```

## Environment Variables Template

```bash
# Server wallet (receives payments)
PAY_TO=0xYourEthereumWalletAddress
PAY_TO_SOLANA=YourSolanaWalletAddress

# Facilitator
FACILITATOR_URL=https://x402.org/facilitator

# CDP API keys (mainnet only)
CDP_API_KEY_ID=your-api-key-id
CDP_API_KEY_SECRET=your-api-key-secret

# Server
PORT=4021
NODE_ENV=development
```
