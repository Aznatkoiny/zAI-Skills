# Client-Side Implementation Patterns

## Table of Contents

1. [Fetch Client](#fetch-client)
2. [Axios Client](#axios-client)
3. [Multi-Chain Client (EVM + Solana)](#multi-chain-client)
4. [Manual Client (Core Only)](#manual-client)
5. [EVM Wallet Setup](#evm-wallet-setup)
6. [Solana Wallet Setup](#solana-wallet-setup)
7. [Lifecycle Hooks](#lifecycle-hooks)
8. [Network Preferences](#network-preferences)
9. [Error Handling](#error-handling)
10. [Environment Variables Template](#env-template)

## Fetch Client

Source: `examples/typescript/clients/fetch/`

```typescript
import { wrapFetchWithPayment } from "@x402/fetch";
import { x402Client, x402HTTPClient } from "@x402/core/client";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

// Create signer from private key
const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);

// Create x402 client and register EVM scheme
const client = new x402Client();
registerExactEvmScheme(client, { signer });

// Wrap native fetch — 402 responses handled automatically
const fetchWithPayment = wrapFetchWithPayment(fetch, client);

const response = await fetchWithPayment("http://localhost:4021/weather", {
  method: "GET",
});
const data = await response.json();
console.log("Response:", data);

// Read payment settlement receipt from headers
if (response.ok) {
  const httpClient = new x402HTTPClient(client);
  const paymentResponse = httpClient.getPaymentSettleResponse(
    (name) => response.headers.get(name),
  );
  console.log("Tx hash:", paymentResponse?.txHash);
}
```

## Axios Client

Source: `examples/typescript/clients/axios/`

```typescript
import { x402Client, wrapAxiosWithPayment, x402HTTPClient } from "@x402/axios";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";
import axios from "axios";

const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);

const client = new x402Client();
registerExactEvmScheme(client, { signer });

// Wrap an Axios instance
const api = wrapAxiosWithPayment(
  axios.create({ baseURL: process.env.RESOURCE_SERVER_URL }),
  client,
);

const response = await api.get(process.env.ENDPOINT_PATH!);
console.log("Response:", response.data);

// Read settlement receipt
const httpClient = new x402HTTPClient(client);
const paymentResponse = httpClient.getPaymentSettleResponse(
  (name) => response.headers[name.toLowerCase()],
);
console.log("Settled:", paymentResponse);
```

## Multi-Chain Client

Source: `examples/typescript/clients/mcp/` pattern

Handle both EVM and Solana endpoints with one client — the SDK auto-selects based on server requirements.

```typescript
import { wrapFetchWithPayment } from "@x402/fetch";
import { x402Client } from "@x402/core/client";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { registerExactSvmScheme } from "@x402/svm/exact/client";
import { privateKeyToAccount } from "viem/accounts";
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { base58 } from "@scure/base";

// EVM signer
const evmSigner = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);

// Solana signer (64-byte secret key in base58)
const svmSigner = await createKeyPairSignerFromBytes(
  base58.decode(process.env.SOLANA_PRIVATE_KEY!),
);

// Register both schemes
const client = new x402Client();
registerExactEvmScheme(client, { signer: evmSigner });
registerExactSvmScheme(client, { signer: svmSigner });

const fetchWithPayment = wrapFetchWithPayment(fetch, client);

// Client auto-selects correct scheme based on server's network in PAYMENT-REQUIRED
const evmResponse = await fetchWithPayment("https://evm-api.example.com/data");
const svmResponse = await fetchWithPayment("https://solana-api.example.com/data");
```

## Manual Client

Source: `examples/typescript/clients/custom/`

Full control over the 402 flow using only `@x402/core`. No interceptors.

```typescript
import { x402Client, x402HTTPClient } from "@x402/core/client";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const client = new x402Client();
registerExactEvmScheme(client, { signer });
const httpClient = new x402HTTPClient(client);

// Step 1: Make initial request
const response = await fetch("http://localhost:4021/weather");

if (response.status === 402) {
  // Step 2: Parse payment requirements from header
  const requirements = httpClient.getPaymentRequirements(
    (name) => response.headers.get(name),
  );

  // Step 3: Select a requirement and create payment
  const selectedRequirement = requirements[0];
  const paymentPayload = await client.createPayment(selectedRequirement);

  // Step 4: Encode as header value
  const paymentHeader = httpClient.encodePaymentHeader(paymentPayload);

  // Step 5: Retry with payment
  const paidResponse = await fetch("http://localhost:4021/weather", {
    headers: { "PAYMENT-SIGNATURE": paymentHeader },
  });

  // Step 6: Read settlement receipt
  const receipt = httpClient.getPaymentSettleResponse(
    (name) => paidResponse.headers.get(name),
  );
  console.log("Paid! Tx:", receipt?.txHash);

  return paidResponse.json();
}
```

## EVM Wallet Setup

Requires `viem` peer dependency.

```typescript
import { privateKeyToAccount } from "viem/accounts";

// From 0x-prefixed hex private key
const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);

// The signer provides:
// - signer.address: string (e.g., "0x1234...")
// - signer.signTypedData(domain, types, message): Promise<string>
```

**Generate a new wallet for testing:**
```typescript
import { generatePrivateKey, privateKeyToAccount } from "viem/accounts";

const privateKey = generatePrivateKey();
const account = privateKeyToAccount(privateKey);
console.log("Address:", account.address);
console.log("Private key:", privateKey); // Save this securely
```

## Solana Wallet Setup

Requires `@solana/kit` and `@scure/base` peer dependencies.

```typescript
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { base58 } from "@scure/base";

// From base58-encoded 64-byte secret key (private key + public key)
const signer = await createKeyPairSignerFromBytes(
  base58.decode(process.env.SOLANA_PRIVATE_KEY!),
);

// The signer provides:
// - signer.address: Address (base58 string)
// - signer.signTransaction(tx): Promise<SignedTransaction>
```

## Lifecycle Hooks

Source: `examples/typescript/clients/advanced/`

Inject custom logic before/after payment creation.

```typescript
const client = new x402Client();
registerExactEvmScheme(client, { signer });

// Before payment: validate, log, or reject
client.onBeforePayment((details) => {
  console.log(`About to pay ${details.amount} to ${details.payTo}`);
  // Return true to proceed, false to abort
  return details.amount < maxAllowed;
});

// After payment: track receipts
client.onAfterPayment((result) => {
  console.log(`Payment created: ${JSON.stringify(result)}`);
  metrics.increment("x402.payments_created");
});

// On error: custom error handling
client.onPaymentError((error) => {
  console.error(`Payment failed: ${error.message}`);
  alerting.notify("x402-payment-failure", error);
});
```

## Network Preferences

Source: `examples/typescript/clients/advanced/`

Configure preferred networks with fallbacks. SDK picks the best match from server's `accepts` array.

```typescript
const client = new x402Client();
registerExactEvmScheme(client, { signer: evmSigner });
registerExactSvmScheme(client, { signer: svmSigner });

// Prefer Base Sepolia, fall back to any EVM, then Solana
client.setNetworkPreferences([
  "eip155:84532",  // First choice
  "eip155:*",      // Any EVM network
  "solana:*",      // Any Solana network
]);
```

## Error Handling

Common error patterns when interacting with x402-protected endpoints.

```typescript
try {
  const response = await fetchWithPayment("https://api.example.com/paid");

  if (!response.ok && response.status !== 402) {
    throw new Error(`Server error: ${response.status}`);
  }

  return await response.json();
} catch (error) {
  if (error.message?.includes("insufficient funds")) {
    console.error("Wallet needs more USDC. Fund via Circle faucet for testnet.");
  } else if (error.message?.includes("No matching scheme")) {
    console.error("Client doesn't support any of the server's accepted networks.");
  } else if (error.message?.includes("signature")) {
    console.error("Payment signature was rejected — check private key and network.");
  } else if (error.message?.includes("timeout")) {
    console.error("Payment or settlement timed out.");
  }
  throw error;
}
```

**Checking if an endpoint requires payment (preflight):**
```typescript
const checkResponse = await fetch(url, { method: "HEAD" });
if (checkResponse.status === 402) {
  const requirementsHeader = checkResponse.headers.get("PAYMENT-REQUIRED");
  const requirements = JSON.parse(atob(requirementsHeader!));
  const costUSDC = parseInt(requirements.accepts[0].maxAmountRequired) / 1_000_000;
  console.log(`This endpoint costs $${costUSDC} USDC`);
}
```

## Environment Variables Template

```bash
# Wallet keys
EVM_PRIVATE_KEY=0x...          # 0x-prefixed hex
SOLANA_PRIVATE_KEY=...          # base58, 64 bytes

# Target server
RESOURCE_SERVER_URL=http://localhost:4021
ENDPOINT_PATH=/weather
```
