# x402 deployment: testnet, mainnet, keys

Checked against x402 2.28.0 and `@coinbase/cdp-sdk` 1.58.0 (October 2026).

## Contents
- Testnet setup and faucets
- Keys: generating, storing, funding
- Moving to mainnet (confirm with the user first)
- Security checklist
- Granting access after payment (sessions)
- Troubleshooting

## Testnet setup and faucets

| Setting | Value |
|---|---|
| Facilitator | `https://x402.org/facilitator` (free, no keys) |
| EVM network | `eip155:84532` (Base Sepolia) |
| Solana network | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` (Devnet) |
| Test USDC | https://faucet.circle.com: pick the network and USDC; 20 USDC per request, one request per network every 2 hours |

A seller needs only a receiving address (`PAY_TO`). A buyer needs a private key holding test USDC. Exact payments on EVM are gasless for the payer, so a Base Sepolia buyer doesn't need ETH. A Solana devnet wallet may need a little SOL (`solana airdrop 1`) depending on the setup.

## Keys: generating, storing, funding

When you generate a key for the user, write it straight into `.env` and print only the address, so the key never appears in the conversation or in shell history:

```typescript
// scripts/new-wallet.ts — run once with: npx tsx scripts/new-wallet.ts
import { appendFileSync, chmodSync, existsSync, readFileSync } from "node:fs";
import { generatePrivateKey, privateKeyToAccount } from "viem/accounts";

if (existsSync(".env") && /EVM_PRIVATE_KEY=0x/.test(readFileSync(".env", "utf8"))) {
  throw new Error(".env already has EVM_PRIVATE_KEY; not overwriting it");
}
const key = generatePrivateKey();
appendFileSync(".env", `EVM_PRIVATE_KEY=${key}\n`);
chmodSync(".env", 0o600);
console.log("New wallet address (fund this from the faucet):", privateKeyToAccount(key).address);
```

Make sure `.env` is in `.gitignore` before anything is committed. In production, keep keys in a secret manager rather than a file, and give each agent and environment its own wallet funded with only what it needs.

## Moving to mainnet

This is the point where real money moves. Before making any of these changes, tell the user what will change, which wallet will pay or receive, and how spending is capped, and get an explicit yes.

1. **Network IDs:** `eip155:84532` becomes `eip155:8453` (Base); Solana Devnet becomes `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp`.
2. **Facilitator:** the x402.org facilitator is for testnets. Use Coinbase's CDP facilitator, which authenticates with a CDP API key (create one at https://portal.cdp.coinbase.com):
   ```typescript
   import { createCdpFacilitatorClient } from "@coinbase/cdp-sdk/x402";
   import { x402ResourceServer } from "@x402/core/server";
   import { ExactEvmScheme } from "@x402/evm/exact/server";

   // Reads CDP_API_KEY_ID and CDP_API_KEY_SECRET from the environment and signs requests for you.
   const facilitator = createCdpFacilitatorClient();
   const server = new x402ResourceServer(facilitator).register("eip155:8453", new ExactEvmScheme());
   ```
   Don't build CDP auth headers by hand; CDP uses short-lived JWTs that the helper generates. CDP pricing: the first 1,000 settled transactions each month are free, then $0.001 each; verification is free.
3. **Buyers:** mainnet USDC in the paying wallet, and spend controls sized for real money (`client-patterns.md`).

Keep testnet and mainnet configuration separate (for example, `NETWORK` and `FACILITATOR` chosen from an environment variable that defaults to testnet), so a missing variable never sends a development build to mainnet.

## Security checklist

- `.env` gitignored and `chmod 600`; no keys in code, logs, error messages, or tool output.
- Each paying client has `setSpendControls` and, for agents, a total budget and an iteration cap.
- The seller checks `settle` succeeded before granting anything durable.
- Prices that depend on the request are clamped to a sane range.
- Paid API responses and discovery listings are handled as untrusted data in any agent.
- Wallet balances are monitored, with an alert on unusual spend.

## Granting access after payment (sessions)

To let a buyer pay once and then use the resource for a while, issue a session token only after settlement succeeds:

```typescript
const settled = await resourceServer.settlePayment(paymentPayload, requirements);
if (!settled.success) return res.status(402).json({ error: settled.errorReason ?? "payment did not settle" });
res.cookie("x402_session", signSession({ payer: settled.payer, expires: Date.now() + 24 * 3600_000 }), {
  httpOnly: true, secure: true, sameSite: "strict",
});
```

Sign the token (an HMAC or JWT over payer and expiry) so it can't be forged, and check it before the payment middleware runs. The official `servers/sign-in-with-x` example shows a wallet-signature login for returning buyers.

## Troubleshooting

| Symptom | Usual cause |
|---|---|
| Client error `No client registered for scheme ... and network ...` | Server and client disagree on network or scheme (often testnet vs mainnet) |
| `paymentStatus: "settle_failed"` | Payer has too little USDC on that network, or the authorization expired |
| CDP facilitator returns 401 | `CDP_API_KEY_ID` / `CDP_API_KEY_SECRET` missing or wrong; use `createCdpFacilitatorClient()` |
| Receipt fields print `undefined` | Code written for V1 (`txHash`); V2 uses `transaction` and `network` |
| Buyer refuses to pay a price above $1 | Default client spend controls; the buyer must raise `maxAmountPerPayment` |
