# TokenLaunchBot

A Telegram bot that guides users through creating and deploying SPL tokens on the Solana blockchain.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server + Telegram bot (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- Required env: `TELEGRAM_BOT_TOKEN`, `WALLET_ADDRESS`, `PRIVATE_KEY`

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- Telegram: Telegraf v4 (long polling)
- Blockchain: Solana Mainnet (`@solana/web3.js`, `@solana/spl-token`)
- Build: esbuild (ESM bundle)

## Where things live

- `artifacts/api-server/src/bot/` — all Telegram bot code
  - `handlers.ts` — main bot logic and step machine
  - `solana.ts` — Solana/SPL token deployment
  - `messages.ts` — message formatting
  - `keyboards.ts` — Telegraf reply/inline keyboards
  - `session.ts` — session types and defaults
  - `index.ts` — bot launcher

## Architecture decisions

- Bot uses Telegraf session middleware for per-user state (step machine).
- Deployment wallet is fixed via env vars — users cannot change it.
- Private key is only used to sign transactions; never logged or exposed.
- Bot runs via long polling inside the same Express process.
- Solana mainnet RPC is public endpoint; upgrade to a private RPC for production.

## Product

- Users interact via Telegram commands/buttons to configure an SPL token.
- Required fields: Name, Symbol, Supply, Decimals.
- Optional fields: Description, Logo URL, Website, Telegram, Twitter.
- Authority settings (revoke mint/freeze) configurable via inline keyboard.
- Deployment review screen shown before any transaction is signed.
- Deployment fee: 5 SOL minimum. Bot checks wallet balance before proceeding.
- On success: mint address, transaction signature, and Solscan link returned.

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- `PRIVATE_KEY` must be base58-encoded (standard Solana format from Phantom/Solflare export).
- The public RPC (`api.mainnet-beta.solana.com`) may rate-limit under load — use a private RPC (Helius, QuickNode) in production.
- `bigint: Failed to load bindings` warning at startup is harmless — pure JS fallback is used.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
