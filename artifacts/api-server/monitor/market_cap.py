import aiohttp
from utils.logger import logger

PUMPFUN_API = "https://frontend-api.pump.fun/coins"
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens"


class MarketCapMonitor:
    def __init__(self):
        self._targets: dict[str, dict] = {}

    def add_target(
        self,
        mint_address: str,
        target_usd: float,
        chat_id: int,
        symbol: str,
        launchpad: str,
        wallet_address: str,
    ) -> None:
        if target_usd <= 0:
            return
        self._targets[mint_address] = {
            "target_usd": target_usd,
            "chat_id": chat_id,
            "symbol": symbol,
            "launchpad": launchpad,
            "wallet_address": wallet_address,
            "fired": False,
        }
        logger.info(f"Market cap monitor: tracking {symbol} ({mint_address}) target=${target_usd:,.0f}")

    def remove_target(self, mint_address: str) -> None:
        self._targets.pop(mint_address, None)

    async def _get_pumpfun_mcap(self, mint_address: str) -> float | None:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{PUMPFUN_API}/{mint_address}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        usd_market_cap = data.get("usd_market_cap")
                        if usd_market_cap is not None:
                            return float(usd_market_cap)
        except Exception as e:
            logger.debug(f"Pump.fun mcap fetch error for {mint_address}: {e}")
        return None

    async def _get_dexscreener_mcap(self, mint_address: str) -> float | None:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{DEXSCREENER_API}/{mint_address}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pairs = data.get("pairs") or []
                        if pairs:
                            fdv = pairs[0].get("fdv")
                            if fdv is not None:
                                return float(fdv)
        except Exception as e:
            logger.debug(f"DEX Screener mcap fetch error for {mint_address}: {e}")
        return None

    async def poll(self, bot) -> None:
        if not self._targets:
            return

        for mint_address, info in list(self._targets.items()):
            if info["fired"]:
                continue

            mcap = None
            if info["launchpad"] == "pumpfun":
                mcap = await self._get_pumpfun_mcap(mint_address)
            if mcap is None:
                mcap = await self._get_dexscreener_mcap(mint_address)

            if mcap is None:
                logger.debug(f"Market cap unavailable for {mint_address}")
                continue

            target = info["target_usd"]
            logger.debug(f"{info['symbol']}: mcap=${mcap:,.0f} | target=${target:,.0f}")

            if mcap >= target:
                info["fired"] = True
                logger.info(f"Market cap target hit: {info['symbol']} ${mcap:,.0f} >= ${target:,.0f}")

                if info["launchpad"] == "pumpfun":
                    try:
                        from solana_client.launchpad import sell_all_pumpfun
                        sig = await sell_all_pumpfun(mint_address, info["wallet_address"])
                        from bot.messages import mcap_autosell_message
                        text = mcap_autosell_message(mint_address, sig, mcap, info["symbol"])
                    except Exception as e:
                        logger.error(f"Auto-sell failed for {mint_address}: {e}")
                        from bot.messages import mcap_alert_message
                        text = mcap_alert_message(mint_address, mcap, target, info["symbol"])
                else:
                    from bot.messages import mcap_alert_message
                    text = mcap_alert_message(mint_address, mcap, target, info["symbol"])

                try:
                    await bot.send_message(
                        chat_id=info["chat_id"],
                        text=text,
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logger.warning(f"Failed to send mcap alert to {info['chat_id']}: {e}")

                self._targets.pop(mint_address, None)


market_cap_monitor = MarketCapMonitor()
