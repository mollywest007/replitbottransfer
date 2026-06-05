import time
import aiohttp
from config import DEX_UPDATE_USD, DEX_BOOST_USD, DEX_PRICE_CACHE_SECONDS
from utils.logger import logger

_cache: dict = {
    "sol_usd": 150.0,
    "update_usd": DEX_UPDATE_USD,
    "boost_usd": DEX_BOOST_USD,
    "update_sol": DEX_UPDATE_USD / 150.0,
    "boost_sol": DEX_BOOST_USD / 150.0,
    "last_fetched": 0.0,
}


async def fetch_dex_prices() -> dict:
    now = time.time()
    if now - _cache["last_fetched"] < DEX_PRICE_CACHE_SECONDS:
        return dict(_cache)

    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    raise ValueError(f"CoinGecko HTTP {resp.status}")
                data = await resp.json()
                sol_usd = data.get("solana", {}).get("usd")
                if not sol_usd or float(sol_usd) <= 0:
                    raise ValueError("Invalid SOL price from CoinGecko")

        sol_usd = float(sol_usd)
        _cache.update({
            "sol_usd": sol_usd,
            "update_sol": DEX_UPDATE_USD / sol_usd,
            "boost_sol": DEX_BOOST_USD / sol_usd,
            "last_fetched": now,
        })
        logger.info(f"DEX pricing refreshed — SOL: ${sol_usd:.2f}")
    except Exception as e:
        logger.warning(f"Failed to refresh SOL price: {e} — using cached ${_cache['sol_usd']:.2f}")

    return dict(_cache)
