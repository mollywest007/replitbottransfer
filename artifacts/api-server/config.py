import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# Receiving addresses are public information. Keep the receiving wallet
# separate from any signing wallet managed outside this bot.
RECEIVING_WALLET_ADDRESS = "no463nB9777LFRUEjw5bLssFj5n5YzAmz9HMvrJ3AB6"

SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

DEPLOYMENT_FEE = 2.0
PLATFORM_FEE_USD = 50
DEX_UPDATE_USD = 299
DEX_BOOST_USD = 30
CREATION_BUFFER_SOL = 0.05
PUMPFUN_MIN_SOL = 0.05

POLL_INTERVAL_SECONDS = 30
DEX_PRICE_CACHE_SECONDS = 1800
