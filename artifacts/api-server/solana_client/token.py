from datetime import datetime, timezone
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.message import Message
from solders.transaction import Transaction
from solders.system_program import create_account, CreateAccountParams
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from spl.token.instructions import (
    initialize_mint, InitializeMintParams,
    mint_to, MintToParams,
    burn, BurnParams,
    transfer_checked, TransferCheckedParams,
    set_authority, SetAuthorityParams, AuthorityType,
    get_associated_token_address,
    create_associated_token_account,
)
from config import SOLANA_RPC_URL
from solana_client.wallet import get_keypair
from utils.logger import logger

MINT_LEN = 82
LAMPORTS_PER_SOL = 1_000_000_000


async def get_token_balance(mint_address: str, wallet_address: str) -> dict:
    async with AsyncClient(SOLANA_RPC_URL) as client:
        mint = Pubkey.from_string(mint_address)
        wallet = Pubkey.from_string(wallet_address)
        ata = get_associated_token_address(wallet, mint)

        try:
            account_resp = await client.get_token_account_balance(ata)
            if account_resp.value:
                ui_amount = float(account_resp.value.ui_amount or 0)
                raw_amount = int(account_resp.value.amount)
                decimals = account_resp.value.decimals
                return {"raw_amount": raw_amount, "ui_amount": ui_amount, "decimals": decimals}
        except Exception:
            pass

        return {"raw_amount": 0, "ui_amount": 0.0, "decimals": 9}


async def deploy_token(token_config: dict) -> dict:
    payer = get_keypair()
    mint_kp = Keypair()
    decimals = token_config.get("decimals", 9)
    supply = token_config.get("supply", 1_000_000_000)
    supply_raw = supply * (10 ** decimals)
    revoke_mint = token_config.get("revoke_mint", False)
    revoke_freeze = token_config.get("revoke_freeze", False)

    async with AsyncClient(SOLANA_RPC_URL) as client:
        rent_resp = await client.get_minimum_balance_for_rent_exemption(MINT_LEN)
        lamports_for_mint = rent_resp.value

        blockhash_resp = await client.get_latest_blockhash()
        blockhash = blockhash_resp.value.blockhash

        ata = get_associated_token_address(payer.pubkey(), mint_kp.pubkey())

        instructions = [
            create_account(CreateAccountParams(
                from_pubkey=payer.pubkey(),
                to_pubkey=mint_kp.pubkey(),
                lamports=lamports_for_mint,
                space=MINT_LEN,
                owner=TOKEN_PROGRAM_ID,
            )),
            initialize_mint(InitializeMintParams(
                program_id=TOKEN_PROGRAM_ID,
                mint=mint_kp.pubkey(),
                decimals=decimals,
                mint_authority=payer.pubkey(),
                freeze_authority=None if revoke_freeze else payer.pubkey(),
            )),
            create_associated_token_account(
                payer=payer.pubkey(),
                owner=payer.pubkey(),
                mint=mint_kp.pubkey(),
            ),
            mint_to(MintToParams(
                program_id=TOKEN_PROGRAM_ID,
                mint=mint_kp.pubkey(),
                dest=ata,
                mint_authority=payer.pubkey(),
                amount=supply_raw,
                signers=[],
            )),
        ]

        if revoke_mint:
            instructions.append(set_authority(SetAuthorityParams(
                program_id=TOKEN_PROGRAM_ID,
                account=mint_kp.pubkey(),
                authority=AuthorityType.MintTokens,
                current_authority=payer.pubkey(),
                new_authority=None,
                signers=[],
            )))

        if revoke_freeze:
            pass  # freeze authority set to None in initialize_mint

        msg = Message.new_with_blockhash(instructions, payer.pubkey(), blockhash)
        tx = Transaction([payer, mint_kp], msg, blockhash)

        logger.info(f"Deploying SPL token: {token_config.get('name')} ({token_config.get('symbol')})")
        resp = await client.send_raw_transaction(bytes(tx))
        sig = str(resp.value)
        await client.confirm_transaction(resp.value, commitment="confirmed")

    mint_address = str(mint_kp.pubkey())
    logger.info(f"Token deployed: {mint_address} | sig: {sig}")
    return {
        "mint_address": mint_address,
        "tx_signature": sig,
        "solscan_url": f"https://solscan.io/token/{mint_address}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


async def burn_tokens(mint_address: str, raw_amount: int) -> str:
    payer = get_keypair()
    mint = Pubkey.from_string(mint_address)
    ata = get_associated_token_address(payer.pubkey(), mint)

    async with AsyncClient(SOLANA_RPC_URL) as client:
        mint_info = await client.get_account_info_json_parsed(mint)
        decimals = mint_info.value.data.parsed["info"]["decimals"] if mint_info.value else 9

        blockhash_resp = await client.get_latest_blockhash()
        blockhash = blockhash_resp.value.blockhash

        ix = burn(BurnParams(
            program_id=TOKEN_PROGRAM_ID,
            account=ata,
            mint=mint,
            owner=payer.pubkey(),
            amount=raw_amount,
            signers=[],
        ))
        msg = Message.new_with_blockhash([ix], payer.pubkey(), blockhash)
        tx = Transaction([payer], msg, blockhash)

        logger.info(f"Burning {raw_amount} tokens of {mint_address}")
        resp = await client.send_raw_transaction(bytes(tx))
        sig = str(resp.value)
        await client.confirm_transaction(resp.value, commitment="confirmed")
        return sig


async def transfer_spl_tokens(mint_address: str, to_address: str, raw_amount: int) -> str:
    payer = get_keypair()
    mint = Pubkey.from_string(mint_address)
    to_pubkey = Pubkey.from_string(to_address)
    from_ata = get_associated_token_address(payer.pubkey(), mint)
    to_ata = get_associated_token_address(to_pubkey, mint)

    async with AsyncClient(SOLANA_RPC_URL) as client:
        mint_info = await client.get_account_info_json_parsed(mint)
        decimals = mint_info.value.data.parsed["info"]["decimals"] if mint_info.value else 9

        blockhash_resp = await client.get_latest_blockhash()
        blockhash = blockhash_resp.value.blockhash

        instructions = []
        to_ata_info = await client.get_account_info(to_ata)
        if to_ata_info.value is None:
            instructions.append(create_associated_token_account(
                payer=payer.pubkey(),
                owner=to_pubkey,
                mint=mint,
            ))

        instructions.append(transfer_checked(TransferCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=from_ata,
            mint=mint,
            dest=to_ata,
            owner=payer.pubkey(),
            amount=raw_amount,
            decimals=decimals,
            signers=[],
        )))

        msg = Message.new_with_blockhash(instructions, payer.pubkey(), blockhash)
        tx = Transaction([payer], msg, blockhash)

        logger.info(f"Transferring {raw_amount} of {mint_address} → {to_address}")
        resp = await client.send_raw_transaction(bytes(tx))
        sig = str(resp.value)
        await client.confirm_transaction(resp.value, commitment="confirmed")
        return sig


async def revoke_mint_authority(mint_address: str) -> str:
    payer = get_keypair()
    mint = Pubkey.from_string(mint_address)

    async with AsyncClient(SOLANA_RPC_URL) as client:
        blockhash_resp = await client.get_latest_blockhash()
        blockhash = blockhash_resp.value.blockhash

        ix = set_authority(SetAuthorityParams(
            program_id=TOKEN_PROGRAM_ID,
            account=mint,
            authority=AuthorityType.MintTokens,
            current_authority=payer.pubkey(),
            new_authority=None,
            signers=[],
        ))
        msg = Message.new_with_blockhash([ix], payer.pubkey(), blockhash)
        tx = Transaction([payer], msg, blockhash)

        logger.info(f"Revoking mint authority: {mint_address}")
        resp = await client.send_raw_transaction(bytes(tx))
        sig = str(resp.value)
        await client.confirm_transaction(resp.value, commitment="confirmed")
        return sig


async def revoke_freeze_authority(mint_address: str) -> str:
    payer = get_keypair()
    mint = Pubkey.from_string(mint_address)

    async with AsyncClient(SOLANA_RPC_URL) as client:
        blockhash_resp = await client.get_latest_blockhash()
        blockhash = blockhash_resp.value.blockhash

        ix = set_authority(SetAuthorityParams(
            program_id=TOKEN_PROGRAM_ID,
            account=mint,
            authority=AuthorityType.FreezeAccount,
            current_authority=payer.pubkey(),
            new_authority=None,
            signers=[],
        ))
        msg = Message.new_with_blockhash([ix], payer.pubkey(), blockhash)
        tx = Transaction([payer], msg, blockhash)

        logger.info(f"Revoking freeze authority: {mint_address}")
        resp = await client.send_raw_transaction(bytes(tx))
        sig = str(resp.value)
        await client.confirm_transaction(resp.value, commitment="confirmed")
        return sig
