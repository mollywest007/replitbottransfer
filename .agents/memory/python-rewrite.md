---
name: Python rewrite architecture
description: TokenLaunchBot fully rewritten from TypeScript/Telegraf to Python/python-telegram-bot. Key decisions and constraints.
---

## Stack
- python-telegram-bot v21 (async, job-queue)
- solana-py 0.34.3 + solders 0.21.0 for blockchain
- spl 0.1.0 for SPL token instructions
- aiohttp for HTTP calls + health check server
- loguru for logging
- python-dotenv for env vars

## Project structure (artifacts/api-server/)
- main.py — asyncio.gather(health_server on $PORT, bot polling)
- config.py — all constants and env vars
- bot/ — session.py, messages.py, keyboards.py, handlers/
- solana_client/ — wallet.py, token.py, launchpad.py
- monitor/ — deposit.py, market_cap.py
- pricing/ — dex.py (CoinGecko)
- utils/ — logger.py (loguru)

## Key decisions
- Health server (aiohttp) runs on PORT (8080) alongside bot — required for Replit artifact system.
- Session stored in context.user_data["session"] (step-machine pattern).
- Pump.fun deployment uses PumpPortal REST API (pumpportal.fun/api/trade-local) since pumpdotfun-sdk is JS-only.
- package.json dev script: `python3 main.py` (packages pre-installed via Nix).
- pip install must NOT be in the dev script — Nix filesystem is immutable.

**Why:** pumpdotfun-sdk has no Python equivalent; PumpPortal provides a language-agnostic HTTP API returning unsigned VersionedTransaction.
**How to apply:** Install packages manually with `python3 -m pip install --break-system-packages -r requirements.txt` if adding new deps.
