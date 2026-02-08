# x402 Protocol Specification

## Table of Contents

1. [Payment Flow with Headers](#payment-flow-with-headers)
2. [Header Structures](#header-structures)
3. [Payment Schemes](#payment-schemes)
4. [CAIP-2 Network Identifiers](#caip-2-network-identifiers)
5. [Facilitator API](#facilitator-api)
6. [V1 vs V2 Differences](#v1-vs-v2-differences)
7. [Data Types Reference](#data-types-reference)

## Payment Flow with Headers

### 1. Initial request (no payment)
```http
GET /weather HTTP/1.1
Host: api.example.com
```

### 2. Server returns 402 with payment requirements
```http
HTTP/1.1 402 Payment Required
PAYMENT-REQUIRED: <base64-encoded JSON PaymentRequired object>
Content-Type: application/json

{"error": "Payment required"}
```

### 3. Client retries with signed payment
```http
GET /weather HTTP/1.1
Host: api.example.com
PAYMENT-SIGNATURE: <base64-encoded JSON PaymentPayload object>
```

### 4. Server returns resource with settlement receipt
```http
HTTP/1.1 200 OK
PAYMENT-RESPONSE: <base64-encoded JSON SettlementResponse object>
Content-Type: application/json

{"weather": "sunny", "temperature": 70}
```

## Header Structures

### PAYMENT-REQUIRED (base64 JSON)
```typescript
{
  x402Version: 2,
  accepts: [
    {
      scheme: "exact",
      network: "eip155:84532",           // CAIP-2 identifier
      maxAmountRequired: "1000",         // Atomic units (0.001 USDC = 1000)
      resource: "/weather",
      description: "Weather data API",
      mimeType: "application/json",
      payTo: "0x1234...abcd",
      maxTimeoutSeconds: 60,
      asset: "0x036CbD53842c5426634e7929541eC2318f3dCF7e", // USDC contract
      extra: { name: "USD Coin", version: "2" },
      outputSchema: null                 // Optional JSON schema
    }
  ],
  error: "X-PAYMENT header is required"  // Optional error message
}
```

### PAYMENT-SIGNATURE (base64 JSON) — EVM Exact Scheme
```typescript
{
  x402Version: 2,
  scheme: "exact",
  network: "eip155:84532",
  payload: {
    signature: "0x...",  // EIP-712 typed data signature
    authorization: {
      from: "0xPayerAddress",
      to: "0xRecipientAddress",
      value: "1000",
      validAfter: "0",
      validBefore: "1735689600",  // Unix timestamp
      nonce: "0x..."              // Random 32-byte hex nonce
    }
  }
}
```

### PAYMENT-RESPONSE (base64 JSON)
```typescript
{
  success: true,
  txHash: "0xabc123...",
  networkId: "eip155:84532"
}
```

## Payment Schemes

### `exact` — Production scheme
Pay a predetermined fixed amount per request. Uses EIP-3009 `TransferWithAuthorization` on EVM (gasless, signature-based). Uses SPL token transfers on Solana.

- **Nonces**: Random 32-byte values (not sequential) — enables concurrent payments.
- **EVM asset**: USDC contract implementing EIP-3009.
- **Solana asset**: SPL token mint address.

### `upto` — Proposed
Pay up to a maximum amount based on actual consumption. Designed for usage-based billing (e.g., LLM token pricing). Not yet implemented in production.

### `deferred` — Proposed by Cloudflare
Batched/delayed settlement for micropayments. Designed for high-frequency, low-value transactions like pay-per-crawl. Settlement happens in aggregate rather than per-request. Supports both stablecoin and traditional payment rails.

## CAIP-2 Network Identifiers

| Network | CAIP-2 Identifier | Environment |
|---------|-------------------|-------------|
| Base Sepolia | `eip155:84532` | Testnet |
| Base Mainnet | `eip155:8453` | Production |
| Ethereum Mainnet | `eip155:1` | Production |
| Polygon Mainnet | `eip155:137` | Production |
| Avalanche Mainnet | `eip155:43114` | Production |
| Arbitrum Mainnet | `eip155:42161` | Production |
| Solana Devnet | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` | Testnet |
| Solana Mainnet | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | Production |

**USDC contract addresses (EVM):**
- Base Sepolia: `0x036CbD53842c5426634e7929541eC2318f3dCF7e`
- Base Mainnet: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`

**USDC mint (Solana):**
- Devnet: `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU`
- Mainnet: `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`

## Facilitator API

Facilitators handle verification and settlement so resource servers don't need blockchain infrastructure.

### POST /verify
Verify a payment is valid without settling it.
```typescript
// Request
{
  x402Version: 2,
  paymentHeader: "<base64 PAYMENT-SIGNATURE value>",
  paymentRequirements: { /* PaymentRequirements object */ }
}
// Response
{
  isValid: boolean,
  invalidReason: string | null
}
```

### POST /settle
Submit payment to the blockchain.
```typescript
// Request (same as /verify)
{
  x402Version: 2,
  paymentHeader: "<base64 PAYMENT-SIGNATURE value>",
  paymentRequirements: { /* PaymentRequirements object */ }
}
// Response
{
  success: boolean,
  txHash: string | null,    // Blockchain transaction hash
  networkId: string | null,  // CAIP-2 network
  error: string | null
}
```

### GET /supported
List supported scheme+network pairs.
```typescript
// Response
{
  kinds: [
    { scheme: "exact", network: "eip155:84532" },
    { scheme: "exact", network: "eip155:8453" },
    { scheme: "exact", network: "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1" }
  ]
}
```

### GET /discovery/resources (Bazaar extension)
Discover x402-protected resources.
```typescript
// Response
{
  x402Version: 2,
  items: [
    {
      resource: "https://api.example.com/weather",
      type: "http",
      accepts: [ /* PaymentRequirements */ ],
      metadata: { description: "...", input: {...}, output: {...} }
    }
  ],
  pagination: { limit: 20, offset: 0, total: 42 }
}
```

**Facilitator URLs:**
- Testnet: `https://x402.org/facilitator` (free, no auth, Base Sepolia + Solana Devnet)
- Mainnet (CDP): `https://api.cdp.coinbase.com/platform/v2/x402` (requires CDP API keys)

## V1 vs V2 Differences

| Aspect | V1 | V2 (Current) |
|--------|-----|--------------|
| Payment header | `X-PAYMENT` | `PAYMENT-SIGNATURE` |
| Requirements | Response body JSON | `PAYMENT-REQUIRED` header |
| Response header | `X-PAYMENT-RESPONSE` | `PAYMENT-RESPONSE` |
| Network format | String (`"base-sepolia"`) | CAIP-2 (`"eip155:84532"`) |
| SDK architecture | Monolithic packages (`x402-express`) | Modular scoped packages (`@x402/express`) |
| Scheme registration | Automatic | Plugin-driven (`registerExactEvmScheme()`) |
| Multi-chain | Manual per-network setup | Native wildcard (`eip155:*`) |
| Extensions | None | Bazaar discovery, lifecycle hooks, modular paywall |
| Multi-facilitator | Single | SDK selects best match based on preferences |

V2 SDK is fully backward-compatible with V1 payloads. V1 package names (`x402-express`, `x402-axios`) are deprecated but still functional.

## Data Types Reference

### PaymentRequirements
```typescript
{
  scheme: string;              // "exact"
  network: string;             // CAIP-2 identifier
  maxAmountRequired: string;   // Atomic units as string (uint256)
  resource: string;            // URL path of protected resource
  description: string;         // Human-readable description
  mimeType: string;            // Response MIME type
  payTo: string;               // Recipient wallet address
  maxTimeoutSeconds: number;   // Max server response time
  asset: string;               // Token contract/mint address
  extra: object | null;        // Scheme-specific data
  outputSchema?: object | null; // Optional JSON schema for response
}
```

### PaymentPayload (PAYMENT-SIGNATURE content)
```typescript
{
  x402Version: number;
  scheme: string;
  network: string;
  payload: object; // Scheme-dependent (see exact scheme above)
}
```
