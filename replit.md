# TokenLaunchBot

A Python Telegram bot that guides users through creating and deploying SPL tokens on the Solana blockchain.

## Run & Operate

- The Replit workflow runs `cd artifacts/api-server && python3 main.py`.
- The health endpoint is available at `/api/healthz` on the configured application port.
- Python dependencies are pinned in `artifacts/api-server/requirements.txt`.
- Required secret: `TELEGRAM_BOT_TOKEN`.
- Receiving wallet: `no463nB9777LFRUEjw5bLssFj5n5YzAmz9HMvrJ3AB6` (receiving address).

## Stack

- Python 3.12 with `python-telegram-bot` 21
- Solana Python client, Solders, and SPL helpers
- `aiohttp` health server running alongside Telegram long polling
- `loguru` logging and `python-dotenv` configuration

## Where things live

- `artifacts/api-server/main.py` — health server and bot launcher
- `artifacts/api-server/config.py` — environment-backed configuration
- `artifacts/api-server/bot/` — Telegram session, messages, keyboards, and handlers
- `artifacts/api-server/solana_client/` — wallet, token, and launchpad operations
- `artifacts/api-server/monitor/` — deposit and market-cap monitors
- `artifacts/api-server/pricing/` — DEX pricing helpers

## Architecture decisions

- Bot state is stored per user in `context.user_data["session"]`.
- The health server and Telegram polling run concurrently on the same process.
- The receiving wallet is a fixed receiving address. The bot does not store wallet credentials for receiving SOL.
- Pump.fun deployment uses the language-agnostic PumpPortal API.
- Solana mainnet RPC is public by default; use a private RPC for production workloads.

## Product

- Users configure token name, symbol, supply, decimals, and optional metadata.
- Authority settings can be configured before deployment.
- A review screen is shown before any transaction is signed.
- Successful deployments return the mint address, transaction signature, and Solscan link.

## Security notes

- Store the Telegram bot token in Replit Secrets; do not put it in `.replit` or commit it.
- Keep any wallet signing credentials outside this receiving bot.
- Rotate any credential that has been exposed in chat, source control, or logs.
- The public RPC may rate-limit under load; use a private RPC for production.
