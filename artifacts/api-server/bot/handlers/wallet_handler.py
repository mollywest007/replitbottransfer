"""Wallet info and SOL withdrawal flow."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.session import get_session
from bot.keyboards import main_menu_keyboard, back_cancel_keyboard, confirm_cancel_keyboard
from bot.messages import (
    wallet_message, withdraw_review_message, withdraw_success_message, error_message,
)
from solana_client.wallet import get_wallet_address, get_wallet_balance, withdraw_sol
from config import PRIVATE_KEY
from utils.logger import logger


async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    wallet = get_wallet_address()
    if not wallet:
        await update.message.reply_text(
            "Wallet address not configured. Check your environment variables.",
            reply_markup=main_menu_keyboard(),
        )
        return

    try:
        balance = await get_wallet_balance(wallet)
    except Exception as e:
        logger.warning(f"Could not fetch wallet balance: {e}")
        balance = 0.0

    await update.message.reply_text(
        wallet_message(wallet, balance, bool(PRIVATE_KEY)),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    session["step"] = "withdraw_address"
    session["withdraw"] = {}
    await update.message.reply_text(
        "<b>Withdraw SOL</b>\n\nEnter the destination wallet address:",
        parse_mode="HTML",
        reply_markup=back_cancel_keyboard(),
    )


async def handle_withdraw_address(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    session = get_session(context)
    address = text.strip()
    if len(address) < 32 or len(address) > 44:
        await update.message.reply_text(
            "Invalid Solana address. Please try again.",
        )
        return

    session["withdraw"]["to"] = address
    session["step"] = "withdraw_amount"

    wallet = get_wallet_address()
    try:
        balance = await get_wallet_balance(wallet)
    except Exception:
        balance = 0.0

    await update.message.reply_text(
        f"<b>Withdrawal Amount</b>\n\nWallet balance: <code>{balance:.4f} SOL</code>\n\nHow much SOL to withdraw?",
        parse_mode="HTML",
        reply_markup=back_cancel_keyboard(),
    )


async def handle_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    session = get_session(context)
    try:
        amount = float(text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "Invalid amount. Please enter a positive number like 1.5.",
        )
        return

    wallet = get_wallet_address()
    try:
        balance = await get_wallet_balance(wallet)
    except Exception:
        balance = 0.0

    if amount > balance:
        await update.message.reply_text(
            f"Insufficient balance. You have <code>{balance:.4f} SOL</code> available.",
            parse_mode="HTML",
        )
        return

    session["withdraw"]["amount"] = amount
    session["step"] = "withdraw_confirm"

    await update.message.reply_text(
        withdraw_review_message(session["withdraw"]["to"], amount, balance),
        parse_mode="HTML",
        reply_markup=confirm_cancel_keyboard(),
    )


async def execute_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    to_address = session["withdraw"].get("to")
    amount = session["withdraw"].get("amount")

    if not to_address or not amount:
        session["step"] = "idle"
        await update.message.reply_text(
            "Withdrawal cancelled. Use /withdraw to start again.",
            reply_markup=main_menu_keyboard(),
        )
        return

    session["step"] = "idle"
    await update.message.reply_text("Sending withdrawal...")

    try:
        sig = await withdraw_sol(to_address, amount)
        await update.message.reply_text(
            withdraw_success_message(to_address, amount, sig),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        logger.error(f"Withdrawal failed: {e}")
        await update.message.reply_text(
            error_message(f"Withdrawal failed: {str(e)[:200]}"),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )


async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    session["step"] = "idle"
    await update.message.reply_text(
        "Cancelled.",
        reply_markup=main_menu_keyboard(),
    )
