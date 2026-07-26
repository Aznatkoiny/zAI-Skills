---
description: Generate an x402 payment starter — seller (paid endpoint with 402 flow) or buyer (paying client) — with safe testnet defaults
argument-hint: "[seller | buyer] [evm | svm]"
---
You are scaffolding an x402 protocol starter using the x402-payments skill.

## Arguments

$ARGUMENTS

Parse two choices from the arguments:

- **Role**: `seller` (an API that requires payment) or `buyer` (a client/agent that pays for x402-protected resources).
- **Chain**: `evm` (Base) or `svm` (Solana).

If either is missing, ask the user rather than guessing. Default environment is **testnet** — Base Sepolia (`eip155:84532`) for EVM, Solana Devnet for SVM, facilitator `https://x402.org/facilitator`. Never scaffold mainnet configuration unless explicitly requested (see the safety note below).

## Step 1: Load the skill

Read `${CLAUDE_PLUGIN_ROOT}/skills/x402-payments/SKILL.md` first, then the reference matching the role:

- Seller → `${CLAUDE_PLUGIN_ROOT}/skills/x402-payments/references/server-patterns.md` (Express/Hono/Next.js middleware, multi-route config, facilitator configuration, environment variables template).
- Buyer → `${CLAUDE_PLUGIN_ROOT}/skills/x402-payments/references/client-patterns.md` (fetch/axios wrappers, wallet setup, lifecycle hooks, error handling, environment variables template).
- For header/payload details or CAIP-2 network IDs, consult `${CLAUDE_PLUGIN_ROOT}/skills/x402-payments/references/protocol-spec.md`.

Follow the skill's Critical Implementation Notes exactly — in particular: register schemes **before** wrapping fetch/axios; use V2 headers; dollar-string prices (`"$0.001"`); Node.js v24+ for the TypeScript SDK.

## Step 2: Generate the starter

Create a TypeScript Node project (ask before writing into a non-empty directory):

```
<project>/
├── package.json          # "engines": { "node": ">=24" }
├── tsconfig.json
├── .env.example          # placeholders only — never real keys
├── .gitignore            # must include .env
├── README.md             # run instructions + faucet links
└── src/
    └── index.ts
```

**Seller (`src/index.ts`)** — follow the server-patterns reference for the chosen framework (default Express unless the user names Hono or Next.js):

- `paymentMiddleware` protecting at least one example route with `scheme: "exact"`, a small dollar-string price, the testnet network ID, and `payTo` from `process.env.PAY_TO`.
- `x402ResourceServer` + `HTTPFacilitatorClient` pointed at `https://x402.org/facilitator`.
- Scheme registration for the chosen chain (`registerExactEvmScheme` from `@x402/evm/exact/server`, or the SVM equivalent from `@x402/svm` per the reference).
- The protected route handler returning example JSON.
- Dependencies per the SKILL.md Decision Tree row for the chosen framework and chain.

**Buyer (`src/index.ts`)** — follow the client-patterns reference:

- Signer from `process.env` (`EVM_PRIVATE_KEY` via viem's `privateKeyToAccount` for EVM; the Solana keypair pattern from the reference for SVM).
- `x402Client` with the chain scheme registered, then `wrapFetchWithPayment` — registration first, wrapping second.
- A request to a configurable target URL (default a localhost seller on `:4021`) and printing the payment receipt (`txHash`) via `x402HTTPClient.getPaymentSettleResponse`.
- Basic error handling per the reference (missing funds, no matching scheme, 402 parse failures).

**README.md** should include: install/run commands, how to get testnet USDC (faucet pointers from `${CLAUDE_PLUGIN_ROOT}/skills/x402-payments/references/deployment.md`), and for buyers, how to generate a throwaway testnet key.

## Step 3: Safety note (always include in your output)

State this to the user verbatim in substance:

> This starter is wired for **testnet only** (Base Sepolia / Solana Devnet, x402.org facilitator). Mainnet configuration — real private keys, CDP facilitator credentials, mainnet network IDs — is your explicit opt-in and is deliberately not scaffolded here. When you are ready, follow the testnet-to-mainnet migration steps in the skill's `references/deployment.md`, use a dedicated agent wallet with limited funds, and keep keys in environment variables, never in code or git.

Never write a real private key into any file. `.env.example` gets placeholder values only, and `.gitignore` must exclude `.env` before anything else is committed.
