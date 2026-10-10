# x402 client patterns (buyer side)

Checked against x402 2.28.0. Official examples: `examples/typescript/clients/` in https://github.com/x402-foundation/x402 (`fetch`, `axios`, `advanced/`, `custom`). If the installed version differs, follow the example for that version.

## Contents
- Signers (EVM and Solana)
- fetch and axios
- Reading the result
- Spend limits
- Lifecycle hooks
- Choosing among payment options
- Errors and what they mean
- Environment template

## Signers

```typescript
// EVM (Base, Polygon, Arbitrum, ...)
import { privateKeyToAccount } from "viem/accounts";
const evmSigner = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);

// Solana: base58-encoded 64-byte secret key
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { base58 } from "@scure/base";
const svmSigner = await createKeyPairSignerFromBytes(base58.decode(process.env.SVM_PRIVATE_KEY!));
```

Check for the variables before using them and fail with a message that names the missing one; the official examples do this, and it saves the user a confusing stack trace. Register Solana only if the user has a Solana key, so an EVM-only setup doesn't crash at startup.

## fetch and axios

```typescript
import { x402Client, wrapFetchWithPayment } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { ExactSvmScheme } from "@x402/svm/exact/client";

const client = new x402Client().register("eip155:*", new ExactEvmScheme(evmSigner));
if (svmSigner) client.register("solana:*", new ExactSvmScheme(svmSigner));
client.setSpendControls({ maxAmountPerPayment: "$0.10" });

const fetchWithPayment = wrapFetchWithPayment(fetch, client);
const response = await fetchWithPayment("https://api.example.com/paid");
```

For axios, import `x402Client` and `wrapAxiosWithPayment` from `@x402/axios` and wrap an axios instance: `wrapAxiosWithPayment(axios.create(), client)`. Register schemes before wrapping. To also pay `upto` (metered) prices, register `UptoEvmScheme` / `UptoSvmScheme` from `@x402/evm/upto/client` and `@x402/svm/upto/client`.

## Reading the result

```typescript
import { x402HTTPClient } from "@x402/fetch";

const result = await new x402HTTPClient(client).processResponse(response);
// result.status        HTTP status
// result.paymentStatus "settled" | "settle_failed" | "payment_required" | "none"
// result.body          parsed body
// result.header        SettleResponse (on success) or PaymentRequired (on 402)
if (result.paymentStatus === "settled") {
  const receipt = result.header as { transaction: string; network: string };
  console.log("Paid in", receipt.transaction, "on", receipt.network);
}
```

`getPaymentSettleResponse(name => response.headers.get(name))` returns just the receipt, but it throws when the response has no `PAYMENT-RESPONSE` header (a free route, or a failed request), so check `response.ok` first or use `processResponse`. The receipt fields are `transaction` and `network`; `txHash` was V1.

## Spend limits

A paying client should always have limits. The SDK enforces a per-payment cap and an asset allowlist, and by default it pays only in its recognized default assets (mainly USD stablecoins), up to $1 per payment.

```typescript
client.setSpendControls({
  maxAmountPerPayment: "$0.05",   // USD cap on recognized default assets; false removes the cap
  allowedAssets: [
    // other tokens must be listed; their caps are integer atomic units, not dollars
    { network: "eip155:8453", asset: "0xTokenAddress", maxAmountPerPayment: "50000" },
  ],
});
```

There's no built-in total budget. For a running total, use a `onBeforePaymentCreation` hook (below). Remember that `amount` in requirements is a string in **atomic units**: for USDC (6 decimals) `"1000"` is $0.001, so convert before comparing with a dollar figure.

## Lifecycle hooks

```typescript
let spentAtomic = 0n;
const budgetAtomic = 1_000_000n; // $1.00 of USDC

client
  .onBeforePaymentCreation(async ({ selectedRequirements }) => {
    const amount = BigInt(selectedRequirements.amount);
    if (spentAtomic + amount > budgetAtomic) {
      return { abort: true, reason: `budget exhausted (${spentAtomic} of ${budgetAtomic} atomic units used)` };
    }
  })
  .onAfterPaymentCreation(async ({ selectedRequirements }) => {
    spentAtomic += BigInt(selectedRequirements.amount); // counts signed payments; see note
  })
  .onPaymentCreationFailure(async ({ error }) => {
    console.error("payment creation failed:", error);
  });
```

The hooks fire around *creating* the signed payment. A signed payment can still fail to settle, so for exact accounting, record spend from the settled receipt (`processResponse`) instead, and persist the running total if the process restarts. An aborted hook surfaces as a thrown `Payment creation aborted: <reason>`. Hooks are named `onBeforePaymentCreation`, `onAfterPaymentCreation`, `onPaymentCreationFailure` and `onPaymentResponse`; older names like `onBeforePayment` or `onPaymentError` don't exist on `x402Client`. See `clients/advanced/hooks.ts`.

## Choosing among payment options

When a server accepts several networks, the client picks the first option it can pay. To prefer one, pass a selector to the constructor (`clients/advanced/preferred-network.ts`):

```typescript
const preferBase = (_version: number, options: PaymentRequirements[]) =>
  options.find(o => o.network === "eip155:8453") ?? options[0];
const client = new x402Client(preferBase);
```

## Errors and what they mean

| Error | Likely cause | What to do |
|---|---|---|
| `No client registered for scheme: X and network: Y` | The server wants a network or scheme you didn't register | Register it (e.g. `"solana:*"`, or `UptoEvmScheme` for `upto`), or tell the user the server can't be paid with their setup |
| `Payment creation aborted: ...` | Your hook or spend controls refused | Expected when the budget is hit; report it, don't retry |
| Settlement fails / `paymentStatus: "settle_failed"` | Insufficient token balance, wrong network, expired authorization | Check the wallet balance on that network; testnet USDC comes from the faucet in `deployment.md` |
| Still 402 after paying | The server rejected the payload (`result.header.error` says why) | Compare the server's `accepts` with what the client registered |

## Environment template

```bash
# .env — gitignored, chmod 600. Testnet keys only until the user opts into mainnet.
EVM_PRIVATE_KEY=0x...            # funded with Base Sepolia USDC
SVM_PRIVATE_KEY=                 # optional, base58
RESOURCE_SERVER_URL=http://localhost:4021
```
