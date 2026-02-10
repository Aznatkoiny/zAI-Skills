---
name: x402-payments
description: |
  Build applications using the x402 protocol — Coinbase's open standard for HTTP-native stablecoin payments using the HTTP 402 status code. Use this skill when:
  - Creating APIs that require USDC payments per request (seller/server side)
  - Building clients or AI agents that pay for x402-protected resources (buyer/client side)
  - Implementing MCP servers with paid tools for Claude Desktop
  - Adding payment middleware to Express, Hono, or Next.js applications
  - Working with Base (EVM) or Solana (SVM) payment flows
  - Building machine-to-machine or agent-to-agent payment systems
  - Integrating micropayments, pay-per-use billing, or paid API access
  Triggers: x402, HTTP 402, payment required, USDC payments, micropayments, pay-per-use API, agentic payments, stablecoin payments, paid API endpoint, paywall middleware
---

# x402 Protocol Skill

## Protocol Overview

x402 embeds stablecoin payments into HTTP by using the 402 "Payment Required" status code. A server responds with payment requirements; the client signs a payment authorization, resubmits the request, and gets the resource after verification and settlement.

**Payment flow:**
1. Client sends HTTP request → Server returns `402` + `PAYMENT-REQUIRED` header (base64 JSON)
2. Client reads requirements, creates signed payment payload
3. Client resubmits request with `PAYMENT-SIGNATURE` header (base64 JSON)
4. Server verifies payment via facilitator `POST /verify`
5. Server performs work, settles via facilitator `POST /settle`
6. Server returns `200` + resource + `PAYMENT-RESPONSE` header (contains txHash)

**Key concepts:**
- **Facilitators** verify and settle payments without holding funds. Use `https://x402.org/facilitator` for testnet, CDP facilitator for mainnet.
- **Schemes**: `exact` (fixed price per request) is the production scheme. `upto` and `deferred` are proposed.
- **Networks**: Identified by CAIP-2 format — `eip155:84532` (Base Sepolia), `eip155:8453` (Base Mainnet), `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` (Solana Devnet).
- **EVM** uses EIP-3009 gasless `TransferWithAuthorization`. **Solana** uses SPL token transfers.

## Quick-Start: Protect an API Endpoint (Seller)

```bash
npm install @x402/express @x402/core @x402/evm
```

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
  res.json({ weather: "sunny", temperature: 70 });
});

app.listen(4021, () => console.log("Server on :4021"));
```

## Quick-Start: Pay for x402 Resources (Buyer/Agent)

```bash
npm install @x402/fetch @x402/core @x402/evm viem
```

```typescript
import { wrapFetchWithPayment } from "@x402/fetch";
import { x402Client, x402HTTPClient } from "@x402/core/client";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const client = new x402Client();
registerExactEvmScheme(client, { signer });

const fetchWithPayment = wrapFetchWithPayment(fetch, client);

const response = await fetchWithPayment("http://localhost:4021/weather");
const data = await response.json();
console.log(data);

// Read payment receipt
const httpClient = new x402HTTPClient(client);
const receipt = httpClient.getPaymentSettleResponse(
  (name) => response.headers.get(name),
);
console.log("Tx:", receipt?.txHash);
```

## Decision Tree

| Decision | Choice | Packages |
|----------|--------|----------|
| **Server: Express** | `paymentMiddleware` from `@x402/express` | `@x402/express @x402/core @x402/evm` |
| **Server: Next.js** | `paymentProxy` from `@x402/next` | `@x402/next @x402/core @x402/evm` |
| **Server: Hono** | `paymentMiddleware` from `@x402/hono` | `@x402/hono @x402/core @x402/evm` |
| **Client: fetch** | `wrapFetchWithPayment` | `@x402/fetch @x402/core @x402/evm viem` |
| **Client: axios** | `wrapAxiosWithPayment` | `@x402/axios @x402/core @x402/evm viem axios` |
| **Client: manual** | `x402Client` + `x402HTTPClient` from `@x402/core` | `@x402/core @x402/evm viem` |
| **Chain: EVM** | `registerExactEvmScheme` | `@x402/evm` + `viem` |
| **Chain: Solana** | `registerExactSvmScheme` | `@x402/svm` + `@solana/kit @scure/base` |
| **Chain: both** | Register both schemes on same client/server | All chain deps |
| **Env: testing** | Facilitator `https://x402.org/facilitator` | Base Sepolia / Solana Devnet |
| **Env: production** | CDP facilitator + API keys | Base Mainnet / Solana Mainnet |
| **Agent: MCP** | MCP server with `@x402/axios` | See `references/agentic-patterns.md` |
| **Agent: Anthropic** | Tool-use with `@x402/fetch` | See `references/agentic-patterns.md` |

## Reference File Navigation

| Task | Read this file |
|------|---------------|
| Headers, payloads, CAIP-2 IDs, facilitator API, V1→V2 changes | `references/protocol-spec.md` |
| Express / Hono / Next.js middleware, multi-route, dynamic pricing | `references/server-patterns.md` |
| Fetch / axios client, wallet setup, lifecycle hooks, error handling | `references/client-patterns.md` |
| AI agent payments, MCP server, tool discovery, budget controls | `references/agentic-patterns.md` |
| Testnet→mainnet migration, CDP keys, faucets, security, sessions | `references/deployment.md` |

## Critical Implementation Notes

1. **Register schemes before wrapping** fetch/axios — order matters.
2. **Two equivalent registration APIs**:
   - Function: `registerExactEvmScheme(server)` / `registerExactEvmScheme(client, { signer })`
   - Method: `server.register("eip155:84532", new ExactEvmScheme())`
3. **V2 headers** (current): `PAYMENT-REQUIRED`, `PAYMENT-SIGNATURE`, `PAYMENT-RESPONSE`.
   V1 headers (legacy): `X-PAYMENT`, `X-PAYMENT-RESPONSE`. SDK is backward-compatible.
4. **Price format**: `"$0.001"` (dollar string) — SDK converts to atomic units (6 decimals for USDC).
5. **Python SDK** uses V1 patterns only. Use TypeScript or Go for V2.
6. **Node.js v24+** required for the TypeScript SDK.
7. **Repo**: `https://github.com/coinbase/x402` — canonical examples in `examples/typescript/`.
8. **Docs**: `https://docs.cdp.coinbase.com/x402/welcome` and `https://x402.gitbook.io/x402`.
