---
description: Generate a working x402 starter on testnet — a seller (an endpoint that charges per request) or a buyer (a client that pays) — on EVM (Base) or Solana
argument-hint: "[seller | buyer] [evm | svm]"
---
Scaffold an x402 starter project using the x402-payments skill bundled with this plugin.

## What the user asked for

$ARGUMENTS

Read two choices from it:

- **Role:** `seller` (an API that charges per request) or `buyer` (a client or agent that pays).
- **Chain:** `evm` (Base) or `svm` (Solana).

If either is missing, default to `seller` and `evm`. Say the assumption in one line and tell the user how to get the other variant (for example `/x402-scaffold buyer evm`). Ask only if their words point both ways.

## Ground rules

The starter is wired for **testnet**: Base Sepolia (`eip155:84532`) or Solana Devnet, with the free facilitator `https://x402.org/facilitator`. Testnet is the safe default because nothing real can be lost while the user learns. If the user explicitly asks for mainnet, still build the testnet starter, add the mainnet settings as a commented-out block taken from the skill's `references/deployment.md`, and explain what switching on would change before you write it.

Keys never go into code, the conversation, or git: `.env.example` holds placeholders, `.env` is gitignored, and the code reads keys from the environment.

## Build it

Read `${CLAUDE_PLUGIN_ROOT}/skills/x402-payments/SKILL.md`, then the reference for the role: `references/server-patterns.md` for a seller, `references/client-patterns.md` for a buyer (both under `${CLAUDE_PLUGIN_ROOT}/skills/x402-payments/`). Base the code on the skill's quick starts, which follow the official x402 examples.

Create this in the current directory (if it isn't empty, ask before writing, or offer a subfolder):

```
package.json      "type": "module", "engines": { "node": ">=22" }, scripts: { "start": "tsx src/index.ts", "typecheck": "tsc --noEmit" }
tsconfig.json     module/moduleResolution "NodeNext", target ES2022, strict
.env.example      placeholders only, with a comment on each variable
.gitignore        node_modules, .env
README.md         what it does, how to run it, how to get test USDC, what to try next
src/index.ts
```

- **Seller:** Express by default (Hono or Next.js if the user names one). One paid route at a small dollar price, a free route for comparison, the testnet network for the chosen chain, and `PAY_TO` (or `SVM_PAY_TO`) read from the environment. If it's unset, exit with a message that names the variable.
- **Buyer:** a signer from `EVM_PRIVATE_KEY` (or the Solana key pattern from the reference), `x402Client` with the chain's scheme registered and `setSpendControls({ maxAmountPerPayment: "$0.01" })`, then `wrapFetchWithPayment`. It requests a configurable URL (default `http://localhost:4021/weather`) and prints `paymentStatus` and the receipt from `x402HTTPClient.processResponse`. If the key is unset, exit with a message that names it.

Dependencies come from the skill's "Choosing pieces" table, plus `dotenv`, `tsx` and `typescript`.

## Check it works

If Node is available, run `node --version`, then `npm install` and `npm run typecheck`. Fix what fails. If Node is older than 22 or missing, say so plainly instead of reporting the project as ready. Don't start a buyer against a real endpoint yourself; that spends funds.

## Tell the user what's next

End with the two or three commands they run, and what they need first:

- **Seller:** a receiving address in `.env`, then `npm start`, then try it with `/x402-scaffold buyer evm` or `curl -i localhost:4021/weather` (they'll see the 402).
- **Buyer:** a testnet key with test USDC from https://faucet.circle.com, a running seller, then `npm start`. If they need a key, offer to generate one the way `references/deployment.md` shows: written straight to `.env`, with only the address shown.

Close with one sentence: this is testnet-only; moving to mainnet means real funds and a CDP API key, and the steps are in the skill's deployment reference.
