"""Verify incoming SOL transfers without requiring a signing key."""
from __future__ import annotations

import asyncio
import os
import sqlite3
from pathlib import Path

import aiohttp
from solders.signature import Signature

from config import RECEIVING_WALLET_ADDRESS, SOLANA_RPC_URL

LAMPORTS_PER_SOL = 1_000_000_000
DB_PATH = Path(
    os.environ.get(
        "DEPOSIT_VERIFICATION_DB",
        Path(__file__).resolve().parents[1] / "data" / "deposit_verifications.sqlite3",
    )
)


class DepositVerificationError(ValueError):
    """A user-facing validation error for a submitted transaction hash."""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS verified_deposits (
            tx_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            lamports INTEGER NOT NULL,
            verified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()
    return connection


def _received_lamports(transaction: dict) -> int:
    meta = transaction.get("meta") or {}
    if meta.get("err") is not None:
        raise DepositVerificationError("That transaction failed on Solana.")

    account_keys = (
        transaction.get("transaction", {})
        .get("message", {})
        .get("accountKeys", [])
    )
    receiving_index = None
    for index, account in enumerate(account_keys):
        address = account.get("pubkey") if isinstance(account, dict) else account
        if address == RECEIVING_WALLET_ADDRESS:
            receiving_index = index
            break

    if receiving_index is None:
        raise DepositVerificationError(
            "That transaction does not send SOL to the receiving address."
        )

    pre_balances = meta.get("preBalances") or []
    post_balances = meta.get("postBalances") or []
    if receiving_index >= len(pre_balances) or receiving_index >= len(post_balances):
        raise DepositVerificationError("The transaction balance data is incomplete.")

    received = int(post_balances[receiving_index]) - int(pre_balances[receiving_index])
    if received <= 0:
        raise DepositVerificationError(
            "That transaction does not contain an incoming SOL deposit."
        )
    return received


async def _fetch_transaction(tx_hash: str) -> dict:
    try:
        signature = str(Signature.from_string(tx_hash.strip()))
    except Exception as exc:
        raise DepositVerificationError("Send a valid Solana transaction hash.") from exc

    payload = {
        "jsonrpc": "2.0",
        "id": "token-launch-bot",
        "method": "getTransaction",
        "params": [
            signature,
            {
                "encoding": "jsonParsed",
                "commitment": "confirmed",
                "maxSupportedTransactionVersion": 0,
            },
        ],
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SOLANA_RPC_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status != 200:
                    raise DepositVerificationError(
                        "Solana could not verify that transaction right now."
                    )
                body = await response.json()
    except DepositVerificationError:
        raise
    except Exception as exc:
        raise DepositVerificationError(
            "Solana could not verify that transaction right now."
        ) from exc

    transaction = body.get("result")
    if not transaction:
        raise DepositVerificationError(
            "Transaction not found yet. Wait for confirmation and try again."
        )
    return transaction


def _claim_hash(tx_hash: str, user_id: int, lamports: int) -> None:
    try:
        with _connect() as connection:
            connection.execute(
                "INSERT INTO verified_deposits (tx_hash, user_id, lamports) VALUES (?, ?, ?)",
                (tx_hash, str(user_id), lamports),
            )
            connection.commit()
    except sqlite3.IntegrityError as exc:
        raise DepositVerificationError(
            "That transaction hash has already been used to verify a deposit."
        ) from exc


async def verify_deposit(tx_hash: str, user_id: int) -> dict:
    """Verify and atomically claim one incoming transaction hash."""
    normalized_hash = tx_hash.strip()
    transaction = await _fetch_transaction(normalized_hash)
    lamports = _received_lamports(transaction)
    await asyncio.to_thread(_claim_hash, normalized_hash, user_id, lamports)
    return {
        "tx_hash": normalized_hash,
        "lamports": lamports,
        "amount_sol": lamports / LAMPORTS_PER_SOL,
    }