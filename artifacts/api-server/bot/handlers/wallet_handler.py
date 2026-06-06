"""Wallet info and SOL withdrawal flow."""
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from bot.session import get_session
from bot.keyboards import main_menu_keyboard, back_cancel_keyboard, confirm_cancel_keyboard, wallet_refresh_keyboard, generate_wallet_keyboard
from bot.messages import (
    wallet_message, no_wallet_message, withdraw_review_message, withdraw_success_message, error_message,
)
from solana_client.wallet import get_wallet_balance, withdraw_sol, get_keypair_from_b58
from monitor.deposit import deposit_monitor
from config import WALLET_ADDRESS, PRIVATE_KEY
from utils.logger import logger


def _user_wallet(context: ContextTypes.DEFAULT_TYPE) -> dict | None:
    return context.user_data.get("user_wallet")


async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Called from text message handler or /wallet command."""
    uw = _user_wallet(context)
    if not uw:
        await update.effective_message.reply_text(
            no_wallet_message(),
            parse_mode="HTML",
            reply_markup=generate_wallet_keyboard(),
        )
        return

    try:
        balance = await get_wallet_balance(uw["address"])
    except Exception as e:
        logger.warning(f"Could not fetch wallet balance: {e}")
        balance = 0.0

    deposit_monitor.subscribe(update.effective_chat.id)

    await update.effective_message.reply_text(
        wallet_message(uw["address"], balance, uw["private_key"]),
        parse_mode="HTML",
        reply_markup=wallet_refresh_keyboard(),
    )


async def handle_generate_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback: reveal the configured deployment wallet to this user."""
    query = update.callback_query
    if not WALLET_ADDRESS:
        await query.answer("Wallet not configured.", show_alert=True)
        return

    uw = {"address": WALLET_ADDRESS, "private_key": PRIVATE_KEY or ""}
    context.user_data["user_wallet"] = uw

    try:
        balance = await get_wallet_balance(uw["address"])
    except Exception:
        balance = 0.0

    deposit_monitor.subscribe(update.effective_chat.id)

    await query.edit_message_text(
        wallet_message(uw["address"], balance, uw["private_key"] or None),
        parse_mode="HTML",
        reply_markup=wallet_refresh_keyboard(),
    )


async def show_wallet_reply(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Called from wallet_refresh callback — edits existing message in place."""
    uw = _user_wallet(context)
    if not uw:
        await query.answer("No wallet found. Use /wallet to generate one.", show_alert=True)
        return

    try:
        balance = await get_wallet_balance(uw["address"])
    except Exception as e:
        logger.warning(f"Could not fetch wallet balance: {e}")
        balance = 0.0

    try:
        await query.edit_message_text(
            wallet_message(uw["address"], balance, uw["private_key"]),
            parse_mode="HTML",
            reply_markup=wallet_refresh_keyboard(),
        )
    except Exception:
        await query.answer(f"Balance: {balance:.4f} SOL", show_alert=True)


async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    session["step"] = "withdraw_address"
    session["withdraw"] = {}
    await update.effective_message.reply_text(
        "<b>Withdraw SOL</b>\n\nEnter the destination wallet address:",
        parse_mode="HTML",
        reply_markup=back_cancel_keyboard(),
    )


async def handle_withdraw_address(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    session = get_session(context)
    address = text.strip()
    if len(address) < 32 or len(address) > 44:
        await update.effective_message.reply_text(
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

    await update.effective_message.reply_text(
        f"<b>Withdrawal Amount</b>\n\n"
        f"Wallet balance: <code>{balance:.4f} SOL</code>\n\n"
        f"How much SOL do you want to withdraw?",
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
        await update.effective_message.reply_text(
            "Invalid amount. Please enter a positive number like 1.5.",
        )
        return

    wallet = get_wallet_address()
    try:
        balance = await get_wallet_balance(wallet)
    except Exception:
        balance = 0.0

    if amount > balance:
        await update.effective_message.reply_text(
            f"Insufficient balance. You have <code>{balance:.4f} SOL</code> available.",
            parse_mode="HTML",
        )
        return

    session["withdraw"]["amount"] = amount
    session["step"] = "withdraw_confirm"

    await update.effective_message.reply_text(
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
        await update.effective_message.reply_text(
            "Withdrawal cancelled. Use /withdraw to start again.",
            reply_markup=main_menu_keyboard(),
        )
        return

    session["step"] = "idle"
    await update.effective_message.reply_text("Sending withdrawal...")

    try:
        sig = await withdraw_sol(to_address, amount)
        await update.effective_message.reply_text(
            withdraw_success_message(to_address, amount, sig),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        logger.error(f"Withdrawal failed: {e}")
        await update.effective_message.reply_text(
            error_message(f"Withdrawal failed: {str(e)[:200]}"),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )


async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    session["step"] = "idle"
    await update.effective_message.reply_text(
        "Cancelled.",
        reply_markup=main_menu_keyboard(),
    )
