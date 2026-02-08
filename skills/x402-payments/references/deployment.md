# Deployment Guide

## Table of Contents

1. [Testnet Development Setup](#testnet-development-setup)
2. [USDC Faucets](#usdc-faucets)
3. [Testnet to Mainnet Migration](#testnet-to-mainnet-migration)
4. [CDP Facilitator Setup](#cdp-facilitator-setup)
5. [Private Key Security](#private-key-security)
6. [Session Cookies (Skip Re-payment)](#session-cookies)
7. [Monitoring and Observability](#monitoring)
8. [Error Response Reference](#error-responses)

## Testnet Development Setup

Testnet requires no API keys. Use these defaults:

| Setting | Testnet Value |
|---------|---------------|
| Facilitator URL | `https://x402.org/facilitator` |
| EVM Network | `eip155:84532` (Base Sepolia) |
| Solana Network | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` (Devnet) |
| USDC | Test tokens from Circle faucet |

**Minimum testnet server `.env`:**
```bash
PAY_TO=0xYourEthereumAddress
```

**Minimum testnet client `.env`:**
```bash
EVM_PRIVATE_KEY=0xYourPrivateKey
RESOURCE_SERVER_URL=http://localhost:4021
```

## USDC Faucets

### Base Sepolia (EVM)
- **Circle Faucet**: https://faucet.circle.com — Select "Base Sepolia" and "USDC". Grants 20 USDC every 2 hours per address.
- Also need Base Sepolia ETH for wallet creation (not for x402 payments — those are gasless). Use any Base Sepolia faucet.

### Solana Devnet
- **Circle Faucet**: https://faucet.circle.com — Select "Solana Devnet" and "USDC".
- Devnet USDC mint: `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU`
- Also need Devnet SOL: `solana airdrop 2` via Solana CLI.

## Testnet to Mainnet Migration

Three changes — no code restructuring needed.

### Step 1: Change network identifiers

```typescript
// Before (testnet)
network: "eip155:84532"      // Base Sepolia
network: "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1"  // Solana Devnet

// After (mainnet)
network: "eip155:8453"       // Base Mainnet
network: "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"  // Solana Mainnet
```

### Step 2: Switch facilitator URL

```typescript
// Before (testnet)
const facilitatorClient = new HTTPFacilitatorClient({
  url: "https://x402.org/facilitator",
});

// After (mainnet — CDP hosted)
const facilitatorClient = new HTTPFacilitatorClient({
  url: "https://api.cdp.coinbase.com/platform/v2/x402",
});
```

### Step 3: Add CDP API credentials

```bash
CDP_API_KEY_ID=your-api-key-id
CDP_API_KEY_SECRET=your-api-key-secret
```

Register mainnet scheme on server:
```typescript
const server = new x402ResourceServer(facilitatorClient)
  .register("eip155:8453", new ExactEvmScheme()); // Base mainnet
```

## CDP Facilitator Setup

The Coinbase Developer Platform facilitator handles verification and settlement for production.

1. **Sign up** at https://cdp.coinbase.com
2. **Create a project** in the CDP dashboard
3. **Generate API credentials** (API Key ID + Secret)
4. **Set environment variables:**
   ```bash
   CDP_API_KEY_ID=your-api-key-id
   CDP_API_KEY_SECRET=your-api-key-secret
   ```

**Pricing:**
- Free tier: 1,000 transactions per month
- After free tier: $0.001 per transaction
- No percentage-based fees

**Facilitator URL:** `https://api.cdp.coinbase.com/platform/v2/x402`

**Server configuration with auth headers:**
```typescript
const facilitatorClient = new HTTPFacilitatorClient({
  url: "https://api.cdp.coinbase.com/platform/v2/x402",
  createAuthHeaders: () => ({
    "X-CDP-API-KEY-ID": process.env.CDP_API_KEY_ID!,
    "X-CDP-API-KEY-SECRET": process.env.CDP_API_KEY_SECRET!,
  }),
});
```

## Private Key Security

**Never hardcode private keys.**

### Development
```bash
# .env file (add to .gitignore!)
EVM_PRIVATE_KEY=0x...
SOLANA_PRIVATE_KEY=...
```

### Production
- Use cloud secret managers (AWS Secrets Manager, GCP Secret Manager, Vault)
- Fund agent wallets with limited amounts only
- Use separate wallets per agent and per environment
- Rotate keys periodically
- Monitor wallet balances with alerts for unusual spending

### Generate a dedicated agent wallet
```typescript
import { generatePrivateKey, privateKeyToAccount } from "viem/accounts";

const key = generatePrivateKey();
const account = privateKeyToAccount(key);
console.log("Agent address:", account.address);
console.log("Private key:", key);
// Fund this address with only the USDC needed for operation
```

## Session Cookies

Source: `examples/typescript/fullstack/next-advanced/`

Issue a session cookie after first payment to avoid charging on every request.

```typescript
import { serialize } from "cookie";

app.get("/premium", async (req, res) => {
  // Check for existing session
  const sessionToken = req.cookies?.["x402-session"];
  if (sessionToken && isValidSession(sessionToken)) {
    return res.json(await generateContent());
  }

  // No session — require payment
  const paymentHeader = req.headers["payment-signature"] as string;
  if (!paymentHeader) {
    return res.status(402).json({ error: "Payment required" });
  }

  const verifyResult = await server.verify(paymentHeader, paymentConfig);
  if (!verifyResult.isValid) {
    return res.status(402).json({ error: verifyResult.invalidReason });
  }

  const settleResult = await server.settle(paymentHeader, paymentConfig);

  // Issue session cookie (valid 24 hours)
  const token = generateSessionToken(settleResult.txHash);
  res.setHeader(
    "Set-Cookie",
    serialize("x402-session", token, {
      httpOnly: true,
      secure: true,
      maxAge: 86400,
      path: "/",
    }),
  );

  res.set("PAYMENT-RESPONSE", settleResult.encoded);
  res.json(await generateContent());
});
```

### Auth-Based Pricing

Source: `examples/typescript/fullstack/auth_based_pricing/`

Charge different prices based on authentication (SIWE + JWT).

```typescript
// Authenticated users: $0.01, Anonymous users: $0.10
app.use((req, res, next) => {
  const jwt = req.headers.authorization?.replace("Bearer ", "");
  req.x402Price = jwt && verifyJWT(jwt) ? "$0.01" : "$0.10";
  next();
});
```

## Monitoring

Track x402 payments with lifecycle hooks.

```typescript
client.onBeforePayment((details) => {
  metrics.increment("x402.payment_required");
  metrics.histogram("x402.amount_usd", parseInt(details.amount) / 1_000_000);
  return true;
});

client.onAfterPayment(() => metrics.increment("x402.payment_success"));
client.onPaymentError((err) => {
  metrics.increment("x402.payment_error");
  console.error(`[x402] ${err.message}`);
});
```

### Key metrics
- `x402.payment_required` — Endpoints hit without payment
- `x402.payment_success` / `x402.payment_error` — Client-side outcomes
- `x402.settlement_success` / `x402.settlement_failure` — Server-side outcomes
- `x402.settlement_duration` — End-to-end time (~2 seconds typical)
- `x402.amount_usd` — Payment size distribution

## Error Response Reference

| HTTP Status | Meaning | Client Action |
|-------------|---------|---------------|
| 402 + `PAYMENT-REQUIRED` header | Payment needed | Parse requirements, sign, retry |
| 402 + `invalidReason` in body | Payment rejected | Check key, network, amount |
| 400 | Malformed payment header | Verify base64 encoding |
| 500 | Settlement failed on-chain | Retry after delay |
| 200 + `PAYMENT-RESPONSE` header | Success | Extract txHash for receipt |

**Common failure causes:**
- Insufficient USDC balance in payer wallet
- Wrong network (client on testnet, server expects mainnet)
- Expired `validBefore` timestamp in payment authorization
- Private key doesn't match the `from` address
- Facilitator unreachable or experiencing downtime
