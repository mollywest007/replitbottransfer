"""
Launchpad integrations.

- Pump.fun: Uses PumpPortal REST API (https://pumpportal.fun/api/trade-local)
  The pumpdotfun-sdk is JS-only; PumpPortal provides a language-agnostic HTTP API
  that returns an unsigned VersionedTransaction which we sign locally.

- Raydium: Standard SPL token deploy. Pool creation is done by the user on Raydium UI.
"""
import io
from datetime import datetime, timezone
import aiohttp
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from config import SOLANA_RPC_URL
from solana_client.wallet import get_keypair
from solana_client.token import deploy_token, get_token_balance
from utils.logger import logger

PUMPPORTAL_URL = "https://pumpportal.fun/api/trade-local"
PUMP_IPFS_URL = "https://pump.fun/api/ipfs"


async def _fetch_logo_bytes(logo_url: str | None) -> tuple[bytes, str]:
    if logo_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(logo_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        content_type = resp.headers.get("content-type", "image/png")
                        return await resp.read(), content_type
        except Exception as e:
            logger.warning(f"Could not fetch logo from {logo_url}: {e}")

    # 1×1 transparent PNG placeholder
    import base64
    placeholder = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return placeholder, "image/png"


async def _upload_ipfs(token_config: dict) -> str:
    logo_bytes, content_type = await _fetch_logo_bytes(token_config.get("logo_url"))
    ext = "jpg" if "jpeg" in content_type or "jpg" in content_type else "png"

    form = aiohttp.FormData()
    form.add_field("name", token_config["name"])
    form.add_field("symbol", token_config["symbol"])
    form.add_field(
        "description",
        token_config.get("description") or f"{token_config['name']} token launched via TokenLaunchBot",
    )
    form.add_field("twitter",  token_config.get("twitter")  or "")
    form.add_field("telegram", token_config.get("telegram") or "")
    form.add_field("website",  token_config.get("website")  or "")
    form.add_field("showName", "true")
    form.add_field(
        "file",
        io.BytesIO(logo_bytes),
        filename=f"logo.{ext}",
        content_type=content_type,
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(PUMP_IPFS_URL, data=form, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                raise RuntimeError(f"IPFS upload failed: HTTP {resp.status} — {await resp.text()}")
            data = await resp.json()
            uri = data.get("metadataUri")
            if not uri:
                raise RuntimeError(f"IPFS upload returned no metadataUri: {data}")
            logger.info(f"IPFS metadata uploaded: {uri}")
            return uri


async def deploy_pumpfun(token_config: dict, creator_buy_sol: float = 0.0) -> dict:
    payer = get_keypair()
    mint_kp = Keypair()

    metadata_uri = await _upload_ipfs(token_config)

    payload = {
        "publicKey": str(payer.pubkey()),
        "action": "create",
        "tokenMetadata": {
            "name": token_config["name"],
            "symbol": token_config["symbol"],
            "uri": metadata_uri,
        },
        "mint": str(mint_kp.pubkey()),
        "denominatedInSol": "true",
        "amount": max(creator_buy_sol, 0.0001),
        "slippage": 10,
        "priorityFee": 0.0005,
        "pool": "pump",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            PUMPPORTAL_URL, json=payload, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"PumpPortal API error: HTTP {resp.status} — {await resp.text()}")
            tx_bytes = await resp.read()

    async with AsyncClient(SOLANA_RPC_URL) as client:
        tx = VersionedTransaction.from_bytes(tx_bytes)
        signed_tx = VersionedTransaction(tx.message, [payer, mint_kp])

        logger.info(f"Sending Pump.fun create tx for mint: {str(mint_kp.pubkey())}")
        resp = await client.send_raw_transaction(bytes(signed_tx))
        sig = str(resp.value)
        await client.confirm_transaction(resp.value, commitment="confirmed")

    mint_address = str(mint_kp.pubkey())
    logger.info(f"Pump.fun token deployed: {mint_address} | sig: {sig}")
    return {
        "mint_address": mint_address,
        "tx_signature": sig,
        "view_url": f"https://pump.fun/coin/{mint_address}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


async def deploy_raydium(token_config: dict, creator_buy_sol: float = 0.0) -> dict:
    result = await deploy_token(token_config)
    mint_address = result["mint_address"]
    return {
        "mint_address": mint_address,
        "tx_signature": result["tx_signature"],
        "raydium_url": f"https://raydium.io/liquidity/create-pool/?mint={mint_address}",
        "solscan_url": result["solscan_url"],
        "timestamp": result["timestamp"],
    }


async def sell_all_pumpfun(mint_address: str, wallet_address: str) -> str:
    payer = get_keypair()
    bal = await get_token_balance(mint_address, wallet_address)

    if bal["raw_amount"] == 0:
        raise RuntimeError("No tokens to sell — creator balance is 0")

    payload = {
        "publicKey": str(payer.pubkey()),
        "action": "sell",
        "mint": mint_address,
        "denominatedInSol": "false",
        "amount": bal["raw_amount"],
        "slippage": 10,
        "priorityFee": 0.0005,
        "pool": "pump",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            PUMPPORTAL_URL, json=payload, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"PumpPortal sell error: HTTP {resp.status} — {await resp.text()}")
            tx_bytes = await resp.read()

    async with AsyncClient(SOLANA_RPC_URL) as client:
        tx = VersionedTransaction.from_bytes(tx_bytes)
        signed_tx = VersionedTransaction(tx.message, [payer])

        logger.info(f"Auto-selling {bal['raw_amount']} tokens of {mint_address}")
        resp = await client.send_raw_transaction(bytes(signed_tx))
        sig = str(resp.value)
        await client.confirm_transaction(resp.value, commitment="confirmed")

    logger.info(f"Pump.fun sell complete: {mint_address} | sig: {sig}")
    return sig
