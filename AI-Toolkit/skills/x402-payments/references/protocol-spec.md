# x402 protocol reference (V2)

Checked against x402 2.28.0 and `specs/x402-specification-v2.md` in https://github.com/x402-foundation/x402 (October 2026). For anything not here, the types in `typescript/packages/core/src/types/` are the source of truth.

## Contents
- HTTP headers
- Data types
- Schemes
- Networks and tokens
- Facilitator API
- V1 vs V2

## HTTP headers

| Header | Direction | Content |
|---|---|---|
| `PAYMENT-REQUIRED` | server → client, with status 402 | base64 JSON `PaymentRequired` |
| `PAYMENT-SIGNATURE` | client → server, on the retry | base64 JSON `PaymentPayload` |
| `PAYMENT-RESPONSE` | server → client, with the resource | base64 JSON `SettleResponse` |

V1 used `X-PAYMENT` and `X-PAYMENT-RESPONSE`, and put the requirements in the response body. Current SDKs and the x402.org facilitator still accept V1, so servers can serve both during a migration.

## Data types

```typescript
type PaymentRequired = {
  x402Version: number;            // 2
  error?: string;                 // why payment is required or was rejected
  resource: ResourceInfo;         // { url, description?, mimeType? }
  accepts: PaymentRequirements[]; // one entry per acceptable way to pay
  extensions?: Record<string, unknown>;
};

type PaymentRequirements = {
  scheme: string;            // "exact", "upto", ...
  network: string;           // CAIP-2, e.g. "eip155:84532"
  asset: string;             // token contract address or SPL mint
  amount: string;            // atomic units (USDC: 6 decimals, so "1000" = $0.001)
  payTo: string;             // recipient address
  maxTimeoutSeconds: number;
  extra: Record<string, unknown>; // scheme-specific, e.g. EIP-712 domain { name, version }
};

type PaymentPayload = {
  x402Version: number;
  resource?: ResourceInfo;
  accepted: PaymentRequirements; // the option the client chose
  payload: Record<string, unknown>; // scheme-specific signature data
  extensions?: Record<string, unknown>;
};

type SettleResponse = {
  success: boolean;
  errorReason?: string;
  errorMessage?: string;
  payer?: string;
  transaction: string;  // on-chain transaction id
  network: string;
  amount?: string;      // actual amount, for schemes like "upto"
  extensions?: Record<string, unknown>;
};
```

Older code and articles use `maxAmountRequired`, a string `resource`, top-level `scheme`/`network` on the payload, and `txHash`/`networkId` on the receipt. Those are V1 names; on a V2 server they read as `undefined`.

## Schemes

- **`exact`**: pay a fixed amount per request. On EVM it uses EIP-3009 `transferWithAuthorization` (gasless for the payer) for tokens that support it, and Permit2 for other ERC-20s (needs a one-time approval). On Solana it uses SPL or Token-2022 transfers.
- **`upto`**: authorize a maximum and settle the amount actually used, for metered work such as LLM tokens. The settled amount comes back in `SettleResponse.amount`.
- **`batch-settlement`**: escrow plus vouchers, settled in batches (EVM).
- **`auth-capture`**: authorize now, capture later.

Specs for each live in `specs/schemes/` in the repo; facilitators list what they support at `GET /supported`.

## Networks and tokens

Networks use CAIP-2 IDs: `eip155:<chainId>` for EVM, `solana:<genesis hash prefix>` for Solana. Common ones:

| Network | CAIP-2 | USDC address / mint |
|---|---|---|
| Base Sepolia (testnet) | `eip155:84532` | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` |
| Base | `eip155:8453` | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| Arbitrum One | `eip155:42161` | `0xaf88d065e77c8cC2239327C5EDb3A432268e5831` |
| Polygon | `eip155:137` | `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359` |
| Solana Devnet (testnet) | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` | `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU` |
| Solana | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |

The protocol works on any EVM chain; what limits you in production is whether your facilitator settles there. The CDP facilitator covers Base, Polygon, Arbitrum, World and Solana (plus their testnets); the x402.org testnet facilitator covers Base Sepolia, Solana Devnet and several other testnets. The full, current token table is in `docs/core-concepts/network-and-token-support.mdx` in the repo. Servers can register a wildcard such as `eip155:*` to accept any EVM network their facilitator supports.

## Facilitator API

Resource servers normally reach these through the SDK (`HTTPFacilitatorClient`), so you rarely build the requests by hand.

| Endpoint | Request | Response |
|---|---|---|
| `POST /verify` | `{ x402Version, paymentPayload, paymentRequirements }` (payload as an object, not the base64 header) | `{ isValid, invalidReason?, invalidMessage?, payer? }` |
| `POST /settle` | same as `/verify` | `SettleResponse` |
| `GET /supported` | — | `{ kinds: [{ x402Version, scheme, network, extra? }], extensions: string[], signers: {...} }` |
| `GET /discovery/resources`, `GET /discovery/search` | Bazaar discovery extension | listings of paid resources, each with `accepts[]` |

Facilitator URLs:
- Testnet: `https://x402.org/facilitator`. Free, no auth; don't use it for mainnet routes.
- Mainnet: CDP at `https://api.cdp.coinbase.com/platform/v2/x402`, which needs JWT auth from a CDP API key. Use `createCdpFacilitatorClient()` from `@coinbase/cdp-sdk/x402` rather than building headers yourself (see `deployment.md`). Other facilitators exist, and a server can also settle on its own (`examples/typescript/servers/self-facilitation`).
- Bazaar discovery listings live on the CDP facilitator: `https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources`. The x402.org facilitator doesn't serve them.

## V1 vs V2

| | V1 | V2 (current) |
|---|---|---|
| Headers | `X-PAYMENT`, `X-PAYMENT-RESPONSE` | `PAYMENT-SIGNATURE`, `PAYMENT-REQUIRED`, `PAYMENT-RESPONSE` |
| Requirements | in the response body | in the `PAYMENT-REQUIRED` header |
| Networks | names like `"base-sepolia"` | CAIP-2 IDs |
| Packages | `x402-express`, `x402-axios`, ... (now under `typescript/packages/legacy`) | scoped `@x402/*` packages |
| Amount field | `maxAmountRequired` | `amount` |
| Receipt | `txHash`, `networkId` | `transaction`, `network`, `payer` |
