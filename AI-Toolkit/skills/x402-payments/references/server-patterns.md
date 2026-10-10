# x402 server patterns (seller side)

Checked against x402 2.28.0. Each pattern points at the official example it follows, in `examples/typescript/servers/` (or `fullstack/`) of https://github.com/x402-foundation/x402. When the user's installed version differs, read that example rather than trusting these snippets.

## Contents
- The pieces
- Express and Hono
- Next.js
- Route config: multiple routes, networks, dynamic prices
- Custom verify and settle (no middleware)
- Listing a resource for discovery
- Environment template

## The pieces

Every seller has the same three parts:
1. A **facilitator client**: `new HTTPFacilitatorClient({ url })` for testnet, or `createCdpFacilitatorClient()` for mainnet (`deployment.md`).
2. A **resource server** with the schemes it accepts: `new x402ResourceServer(facilitator).register(network, new ExactEvmScheme())`. Register a wildcard like `"eip155:*"` to accept any EVM network the facilitator supports.
3. **Middleware** for the framework, configured with which routes cost what.

The middleware returns 402 with requirements for unpaid requests, verifies the payment, runs your handler, settles, and adds `PAYMENT-RESPONSE`. Routes not in the config are free.

## Express and Hono

Express: the quick start in `SKILL.md` (from `servers/express`). Hono is the same shape (from `servers/hono`):

```typescript
import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { paymentMiddleware, x402ResourceServer } from "@x402/hono";
import { HTTPFacilitatorClient } from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";

const facilitator = new HTTPFacilitatorClient({ url: process.env.FACILITATOR_URL ?? "https://x402.org/facilitator" });
const server = new x402ResourceServer(facilitator).register("eip155:84532", new ExactEvmScheme());

const app = new Hono();
app.use(
  paymentMiddleware(
    { "GET /weather": { accepts: { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo: process.env.PAY_TO! } } },
    server,
  ),
);
app.get("/weather", c => c.json({ weather: "sunny" }));
serve({ fetch: app.fetch, port: 4021 });
```

Fastify, CloudFront Lambda@Edge and others have examples next to these.

## Next.js

Next.js 16 renamed middleware to **proxy**: the file is `proxy.ts` and it exports `proxy` (from `fullstack/next/proxy.ts`).

```typescript
// proxy.ts
import { paymentProxy } from "@x402/next";
import { x402ResourceServer, HTTPFacilitatorClient } from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";

const server = new x402ResourceServer(new HTTPFacilitatorClient({ url: process.env.FACILITATOR_URL! }));
server.register("eip155:*", new ExactEvmScheme());

export const proxy = paymentProxy(
  {
    "/protected": {
      accepts: [{ scheme: "exact", price: "$0.001", network: "eip155:84532", payTo: process.env.EVM_ADDRESS! }],
      description: "Premium content",
    },
  },
  server,
);

export const config = { matcher: ["/protected/:path*"] };
```

To charge for a single API route instead, wrap its handler with `withX402(handler, routes, server)` from `@x402/next` (see `fullstack/next/app/api/weather/route.ts`). `withX402` settles only when the handler returns a status below 400, so failed requests aren't charged. `@x402/paywall` adds a browser paywall page for human visitors.

## Route config

```typescript
{
  "GET /weather": {
    accepts: [                                   // one option, or an array
      { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo: evmAddress },
      { scheme: "exact", price: "$0.001", network: "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1", payTo: svmAddress },
    ],
    description: "Weather data",
    mimeType: "application/json",
  },
  "POST /analyze": { accepts: { scheme: "exact", price: "$0.05", network: "eip155:84532", payTo: evmAddress } },
}
```

- Keys are `"METHOD /path"`. Unlisted routes stay free, so don't add entries for free routes.
- `price` takes a dollar string, or a function of the request for **dynamic pricing** (`servers/advanced/dynamic-price.ts`):
  ```typescript
  price: context => (context.adapter.getQueryParam?.("tier") === "premium" ? "$0.005" : "$0.001"),
  ```
  `payTo` can be a function too (`dynamic-pay-to.ts`). Clamp anything taken from the request so a client can't set a zero or negative price.
- For metered work, use the `upto` scheme (`servers/upto`): the client authorizes a maximum and you settle what was used.

## Custom verify and settle (no middleware)

Use this when the framework has no adapter, or when you need control over when settlement happens. It follows `servers/custom/index.ts`; read that file for the full version.

```typescript
const resourceServer = new x402ResourceServer(facilitator).register("eip155:84532", new ExactEvmScheme());
const [requirements] = await resourceServer.buildPaymentRequirements({
  scheme: "exact", price: "$0.001", network: "eip155:84532", payTo: evmAddress,
});

// In the request handler:
const header = req.headers["payment-signature"] as string | undefined;
if (!header) {
  const paymentRequired = resourceServer.createPaymentRequiredResponse([requirements], { url: fullUrl, description: "Weather" });
  res.status(402).set("PAYMENT-REQUIRED", Buffer.from(JSON.stringify(paymentRequired)).toString("base64")).json({});
  return;
}
const paymentPayload = JSON.parse(Buffer.from(header, "base64").toString("utf-8"));
const verified = await resourceServer.verifyPayment(paymentPayload, requirements);
if (!verified.isValid) return res.status(402).json({ error: verified.invalidReason });

const body = await doTheWork();
const settled = await resourceServer.settlePayment(paymentPayload, requirements);
if (!settled.success) return res.status(402).json({ error: settled.errorReason ?? "settlement failed" });
res.set("PAYMENT-RESPONSE", Buffer.from(JSON.stringify(settled)).toString("base64")).json(body);
```

Decide deliberately what happens when settlement fails after the work is done. The safe default above withholds the result. If you return it anyway (for example for slow work where you settle afterwards), you're extending credit, and some requests will go unpaid. Check `settled.success` before granting anything durable, such as a session cookie.

## Listing a resource for discovery

To make a route discoverable by agents through the Bazaar, add the discovery extension to its config (`servers/bazaar`):

```typescript
import { declareDiscoveryExtension } from "@x402/extensions/bazaar";

"GET /weather/:city": {
  accepts: { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo: evmAddress },
  extensions: {
    ...declareDiscoveryExtension({
      pathParamsSchema: { properties: { city: { type: "string" } }, required: ["city"] },
      output: { example: { city: "san-francisco", weather: "foggy" } },
    }),
  },
},
```

Listings are served by the CDP facilitator's discovery endpoint, so they appear when settlements go through CDP.

## Environment template

```bash
# .env — gitignored, chmod 600
PAY_TO=0xYourReceivingAddress        # EVM address that receives payments (no private key needed to receive)
SVM_PAY_TO=YourSolanaAddress         # only if you accept Solana
FACILITATOR_URL=https://x402.org/facilitator   # testnet
# Mainnet only — see deployment.md
# CDP_API_KEY_ID=
# CDP_API_KEY_SECRET=
```

A seller needs only a receiving address. Keep private keys off the server unless it also pays for things.
