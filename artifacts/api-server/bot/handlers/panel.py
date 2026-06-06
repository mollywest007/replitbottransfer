"""Token control panel — balance, burn, transfer, revoke authorities."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.session import get_session
from bot.keyboards import (
    main_menu_keyboard, token_panel_keyboard, burn_confirm_keyboard,
    revoke_confirm_keyboard, back_cancel_keyboard,
)
from bot.messages import (
    panel_message, burn_confirm_message, revoke_confirm_message, error_message,
)
from solana_client.wallet import get_wallet_address
from solana_client.token import (
    get_token_balance, burn_tokens, transfer_spl_tokens,
    revoke_mint_authority, revoke_freeze_authority,
)
from utils.logger import logger


async def show_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    mint = session.get("last_mint")
    symbol = session.get("last_symbol", "TOKEN")

    if not mint:
        await update.effective_message.reply_text(
            "No token deployed yet. Use /create and /launch first.",
            reply_markup=main_menu_keyboard(),
        )
        return

    wallet = get_wallet_address()
    try:
        bal = await get_token_balance(mint, wallet)
        ui_balance = bal["ui_amount"]
    except Exception as e:
        logger.warning(f"Could not fetch token balance: {e}")
        ui_balance = 0.0

    await update.effective_message.reply_text(
        panel_message(mint, symbol, ui_balance),
        parse_mode="HTML",
        reply_markup=token_panel_keyboard(mint),
    )


async def handle_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    session = get_session(context)
    symbol = session.get("last_symbol", "TOKEN")

    if data.startswith("panel_balance:"):
        mint = data.split(":", 1)[1]
        wallet = get_wallet_address()
        try:
            bal = await get_token_balance(mint, wallet)
            ui = bal["ui_amount"]
            await query.edit_message_text(
                panel_message(mint, symbol, ui),
                parse_mode="HTML",
                reply_markup=token_panel_keyboard(mint),
            )
        except Exception as e:
            await query.answer(f"Error fetching balance: {e}", show_alert=True)

    elif data.startswith("panel_burn_half:") or data.startswith("panel_burn_all:"):
        portion = "half" if data.startswith("panel_burn_half:") else "all"
        mint = data.split(":", 1)[1]
        wallet = get_wallet_address()
        try:
            bal = await get_token_balance(mint, wallet)
            raw = bal["raw_amount"]
            ui = bal["ui_amount"]
            burn_raw = raw // 2 if portion == "half" else raw
            burn_ui = ui / 2.0 if portion == "half" else ui

            if burn_raw == 0:
                await query.answer("No tokens to burn!", show_alert=True)
                return

            session["pending_burn_raw"] = burn_raw
            await query.edit_message_text(
                burn_confirm_message(symbol, burn_ui, portion),
                parse_mode="HTML",
                reply_markup=burn_confirm_keyboard(mint, portion),
            )
        except Exception as e:
            await query.answer(f"Error: {e}", show_alert=True)

    elif data.startswith("panel_burn_confirm:"):
        parts = data.split(":", 2)
        portion = parts[1]
        mint = parts[2]
        burn_raw = session.get("pending_burn_raw", 0)
        if burn_raw == 0:
            await query.answer("Invalid burn amount", show_alert=True)
            return
        try:
            sig = await burn_tokens(mint, burn_raw)
            short = f"{sig[:16]}..."
            session["pending_burn_raw"] = 0
            await query.edit_message_text(
                f"<b>🔥 Burn Complete</b>\n\n"
                f"Transaction: <code>{short}</code>\n\n"
                f"Tokens have been permanently destroyed.",
                parse_mode="HTML",
                reply_markup=token_panel_keyboard(mint),
            )
        except Exception as e:
            logger.error(f"Burn failed: {e}", exc_info=True)
            await query.edit_message_text(
                error_message(f"Burn failed: {str(e)[:200]}"),
                parse_mode="HTML",
                reply_markup=token_panel_keyboard(mint),
            )

    elif data.startswith("panel_transfer:"):
        mint = data.split(":", 1)[1]
        session["panel_transfer"] = {"mint": mint}
        session["step"] = "panel_transfer_address"
        await query.edit_message_text(
            "<b>Transfer Tokens</b>\n\nSend the destination wallet address in chat:",
            parse_mode="HTML",
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Enter the destination wallet address:",
            reply_markup=back_cancel_keyboard(),
        )

    elif data.startswith("panel_revoke_mint:"):
        mint = data.split(":", 1)[1]
        await query.edit_message_text(
            revoke_confirm_message("mint", symbol),
            parse_mode="HTML",
            reply_markup=revoke_confirm_keyboard(mint, "mint"),
        )

    elif data.startswith("panel_revoke_freeze:"):
        mint = data.split(":", 1)[1]
        await query.edit_message_text(
            revoke_confirm_message("freeze", symbol),
            parse_mode="HTML",
            reply_markup=revoke_confirm_keyboard(mint, "freeze"),
        )

    elif data.startswith("panel_revoke_confirm:"):
        parts = data.split(":", 2)
        auth_type = parts[1]
        mint = parts[2]
        try:
            if auth_type == "mint":
                sig = await revoke_mint_authority(mint)
            else:
                sig = await revoke_freeze_authority(mint)
            label = "Mint" if auth_type == "mint" else "Freeze"
            short = f"{sig[:16]}..."
            await query.edit_message_text(
                f"<b>🔒 {label} Authority Revoked</b>\n\n"
                f"Transaction: <code>{short}</code>\n\n"
                f"Authority permanently removed.",
                parse_mode="HTML",
                reply_markup=token_panel_keyboard(mint),
            )
        except Exception as e:
            logger.error(f"Revoke failed: {e}", exc_info=True)
            await query.edit_message_text(
                error_message(f"Revoke failed: {str(e)[:200]}"),
                parse_mode="HTML",
                reply_markup=token_panel_keyboard(mint),
            )

    elif data.startswith("panel_cancel:"):
        mint = data.split(":", 1)[1]
        wallet = get_wallet_address()
        try:
            bal = await get_token_balance(mint, wallet)
            ui = bal["ui_amount"]
        except Exception:
            ui = 0.0
        await query.edit_message_text(
            panel_message(mint, symbol, ui),
            parse_mode="HTML",
            reply_markup=token_panel_keyboard(mint),
        )

    else:
        await query.answer("Unknown action.", show_alert=True)


async def handle_panel_transfer_address(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    session = get_session(context)
    address = text.strip()
    if len(address) < 32 or len(address) > 44:
        await update.effective_message.reply_text(
            "Invalid Solana address. Please try again.",
        )
        return
    session["panel_transfer"]["to"] = address
    session["step"] = "panel_transfer_amount"
    await update.effective_message.reply_text(
        "<b>Transfer Amount</b>\n\nHow many tokens to send? Enter a number or type <code>all</code>:",
        parse_mode="HTML",
        reply_markup=back_cancel_keyboard(),
    )


async def handle_panel_transfer_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    session = get_session(context)
    mint = session["panel_transfer"].get("mint")
    to_address = session["panel_transfer"].get("to")
    symbol = session.get("last_symbol", "TOKEN")
    wallet = get_wallet_address()

    try:
        bal = await get_token_balance(mint, wallet)
        raw_amount = bal["raw_amount"]
        decimals = bal["decimals"]
    except Exception as e:
        await update.effective_message.reply_text(
            error_message(f"Could not fetch balance: {e}"),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        session["step"] = "idle"
        return

    if text.strip().lower() == "all":
        send_raw = raw_amount
    else:
        try:
            amount_ui = float(text.strip())
            send_raw = int(amount_ui * (10 ** decimals))
        except ValueError:
            await update.effective_message.reply_text(
                "Invalid amount. Enter a number or 'all'.",
            )
            return

    if send_raw == 0 or send_raw > raw_amount:
        await update.effective_message.reply_text(
            "Amount exceeds your balance or is zero. Please try again.",
        )
        return

    session["step"] = "idle"
    ui_display = send_raw / (10 ** decimals)
    await update.effective_message.reply_text(
        f"Transferring <code>{ui_display:,.4f} {symbol}</code>...",
        parse_mode="HTML",
    )
    try:
        sig = await transfer_spl_tokens(mint, to_address, send_raw)
        short = f"{sig[:16]}..."
        await update.effective_message.reply_text(
            f"<b>✅ Transfer Complete</b>\n\nTransaction: <code>{short}</code>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        logger.error(f"Transfer failed: {e}", exc_info=True)
        await update.effective_message.reply_text(
            error_message(f"Transfer failed: {str(e)[:200]}"),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
