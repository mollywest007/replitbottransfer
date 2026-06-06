import base58
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.message import Message
from solders.transaction import Transaction
from config import SOLANA_RPC_URL, PRIVATE_KEY, WALLET_ADDRESS
from utils.logger import logger

LAMPORTS_PER_SOL = 1_000_000_000


def get_keypair() -> Keypair:
    if not PRIVATE_KEY:
        raise RuntimeError("PRIVATE_KEY not configured")
    decoded = base58.b58decode(PRIVATE_KEY)
    return Keypair.from_bytes(decoded)


def get_keypair_from_b58(private_key_b58: str) -> Keypair:
    decoded = base58.b58decode(private_key_b58)
    return Keypair.from_bytes(decoded)


def generate_new_wallet() -> dict:
    """Generate a fresh Solana keypair. Returns address + base58 private key."""
    kp = Keypair()
    address = str(kp.pubkey())
    private_key = base58.b58encode(bytes(kp)).decode()
    return {"address": address, "private_key": private_key}


def get_wallet_address() -> str:
    return WALLET_ADDRESS


async def get_wallet_balance(address: str) -> float:
    async with AsyncClient(SOLANA_RPC_URL) as client:
        pubkey = Pubkey.from_string(address)
        resp = await client.get_balance(pubkey)
        return resp.value / LAMPORTS_PER_SOL


async def withdraw_sol(to_address: str, amount_sol: float) -> str:
    keypair = get_keypair()
    to_pubkey = Pubkey.from_string(to_address)
    lamports = int(amount_sol * LAMPORTS_PER_SOL)

    async with AsyncClient(SOLANA_RPC_URL) as client:
        blockhash_resp = await client.get_latest_blockhash()
        blockhash = blockhash_resp.value.blockhash

        ix = transfer(TransferParams(
            from_pubkey=keypair.pubkey(),
            to_pubkey=to_pubkey,
            lamports=lamports,
        ))
        msg = Message.new_with_blockhash([ix], keypair.pubkey(), blockhash)
        tx = Transaction([keypair], msg, blockhash)

        resp = await client.send_raw_transaction(bytes(tx))
        sig = str(resp.value)
        await client.confirm_transaction(resp.value, commitment="confirmed")
        logger.info(f"SOL withdrawn: {amount_sol} SOL → {to_address} | sig: {sig}")
        return sig
