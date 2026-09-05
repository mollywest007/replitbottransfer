from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from config import SOLANA_RPC_URL, RECEIVING_WALLET_ADDRESS
from utils.logger import logger

LAMPORTS_PER_SOL = 1_000_000_000


def get_keypair():
    """Signing is intentionally unavailable to this receive-only bot."""
    raise RuntimeError("Transaction signing is disabled; this bot only receives SOL.")


def get_wallet_address() -> str:
    return RECEIVING_WALLET_ADDRESS


async def get_wallet_balance(address: str) -> float:
    async with AsyncClient(SOLANA_RPC_URL) as client:
        pubkey = Pubkey.from_string(address)
        resp = await client.get_balance(pubkey)
        return resp.value / LAMPORTS_PER_SOL
