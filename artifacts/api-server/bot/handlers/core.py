"""Core dispatcher — all commands, message routing, and callback query routing."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.session import get_session, reset_session as do_reset
from bot.keyboards import main_menu_keyboard
from bot.messages import main_menu_message, help_message, review_message, error_message
from solana_client.wallet import get_wallet_address
from utils.logger import logger


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    do_reset(context)
    await update.effective_message.reply_text(
        main_menu_message(),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        help_message(),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    do_reset(context)
    await update.effective_message.reply_text(
        "<b>Session reset.</b>\n\nUse /create to start a new token.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def cmd_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from bot.handlers.create import start_create
    await start_create(update, context)


async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from bot.handlers.wallet_handler import show_wallet
    await show_wallet(update, context)


async def cmd_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from bot.handlers.wallet_handler import start_withdraw
    await start_withdraw(update, context)


async def cmd_launch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    token = session["token"]
    if not token.get("name") or not token.get("symbol"):
        await update.effective_message.reply_text(
            "No token ready. Use /create first.",
            reply_markup=main_menu_keyboard(),
        )
        return
    session["step"] = "authority"
    from bot.handlers.create import show_authority_settings
    await show_authority_settings(update, context)


async def cmd_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    token = session["token"]
    if not token.get("name") or not token.get("symbol"):
        await update.effective_message.reply_text(
            "No token configured yet. Use /create to start.",
            reply_markup=main_menu_keyboard(),
        )
        return
    wallet = get_wallet_address()
    await update.effective_message.reply_text(
        review_message(token, wallet),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from bot.handlers.panel import show_panel
    await show_panel(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    session = get_session(context)
    step = session.get("step", "idle")

    try:
        if text == "Create Token":
            from bot.handlers.create import start_create
            await start_create(update, context)

        elif text == "Wallet Info":
            from bot.handlers.wallet_handler import show_wallet
            await show_wallet(update, context)

        elif text == "Withdraw SOL":
            from bot.handlers.wallet_handler import start_withdraw
            await start_withdraw(update, context)

        elif text == "Review Deployment":
            await cmd_review(update, context)

        elif text == "Launch Token":
            await cmd_launch(update, context)

        elif text == "Token Panel":
            from bot.handlers.panel import show_panel
            await show_panel(update, context)

        elif text == "Help":
            await update.effective_message.reply_text(
                help_message(),
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(),
            )

        elif text == "Reset":
            await cmd_reset(update, context)

        elif text in ("Cancel", "❌ Cancel"):
            from bot.handlers.wallet_handler import cancel_flow
            await cancel_flow(update, context)

        elif text == "◀ Back":
            await _handle_back(update, context, session, step)

        elif text == "Skip" and step == "collecting_optional":
            from bot.handlers.create import skip_optional
            await skip_optional(update, context)

        elif text == "Done with optional fields" and step == "collecting_optional":
            from bot.handlers.create import show_authority_settings
            await show_authority_settings(update, context)

        elif text in ("✅ Confirm", "Confirm Withdrawal") and step == "withdraw_confirm":
            from bot.handlers.wallet_handler import execute_withdrawal
            await execute_withdrawal(update, context)

        elif step == "collecting_required":
            from bot.handlers.create import handle_required_field
            await handle_required_field(update, context, text)

        elif step == "collecting_optional":
            from bot.handlers.create import handle_optional_field
            await handle_optional_field(update, context, text)

        elif step == "creator_buy_custom":
            from bot.handlers.launch import handle_creator_buy_custom_input
            await handle_creator_buy_custom_input(update, context, text)

        elif step == "target_mcap_custom":
            from bot.handlers.launch import handle_target_mcap_custom_input
            await handle_target_mcap_custom_input(update, context, text)

        elif step == "withdraw_address":
            from bot.handlers.wallet_handler import handle_withdraw_address
            await handle_withdraw_address(update, context, text)

        elif step == "withdraw_amount":
            from bot.handlers.wallet_handler import handle_withdraw_amount
            await handle_withdraw_amount(update, context, text)

        elif step == "panel_transfer_address":
            from bot.handlers.panel import handle_panel_transfer_address
            await handle_panel_transfer_address(update, context, text)

        elif step == "panel_transfer_amount":
            from bot.handlers.panel import handle_panel_transfer_amount
            await handle_panel_transfer_amount(update, context, text)

    except Exception as e:
        logger.error(f"Unhandled error in message handler: {e}", exc_info=True)
        try:
            await update.effective_message.reply_text(
                error_message("An unexpected error occurred. Please try again or use /reset."),
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(),
            )
        except Exception:
            pass


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    if session.get("step") == "collecting_optional":
        from bot.handlers.create import handle_optional_photo
        await handle_optional_photo(update, context)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""
    session = get_session(context)

    try:
        if data == "toggle_mint":
            session["token"]["revoke_mint"] = not session["token"].get("revoke_mint", False)
            from bot.keyboards import authority_inline_keyboard
            await query.edit_message_reply_markup(
                reply_markup=authority_inline_keyboard(
                    session["token"]["revoke_mint"],
                    session["token"]["revoke_freeze"],
                )
            )

        elif data == "toggle_freeze":
            session["token"]["revoke_freeze"] = not session["token"].get("revoke_freeze", False)
            from bot.keyboards import authority_inline_keyboard
            await query.edit_message_reply_markup(
                reply_markup=authority_inline_keyboard(
                    session["token"]["revoke_mint"],
                    session["token"]["revoke_freeze"],
                )
            )

        elif data == "authority_done":
            from bot.handlers.launch import initiate_launch
            from bot.keyboards import launchpad_keyboard
            from bot.messages import launchpad_select_message
            session["step"] = "select_launchpad"
            token = session["token"]
            await query.edit_message_text(
                launchpad_select_message(token["name"], token["symbol"]),
                parse_mode="HTML",
                reply_markup=launchpad_keyboard(),
            )

        elif data in ("launch_pumpfun", "launch_raydium"):
            launchpad = "pumpfun" if data == "launch_pumpfun" else "raydium"
            from bot.handlers.launch import handle_launchpad_selected
            await handle_launchpad_selected(update, context, launchpad)

        elif data == "launch_cancel":
            session["step"] = "idle"
            await query.edit_message_text("Launch cancelled. Use /launch to try again.")

        elif data.startswith("cb_buy:"):
            value = data.split(":", 1)[1]
            from bot.handlers.launch import handle_creator_buy_selected
            await handle_creator_buy_selected(update, context, value)

        elif data.startswith("cb_mcap:"):
            value = data.split(":", 1)[1]
            from bot.handlers.launch import handle_target_mcap_selected
            await handle_target_mcap_selected(update, context, value)

        elif data == "dex_toggle_update":
            from bot.handlers.launch import handle_dex_toggle
            await handle_dex_toggle(update, context, "update")

        elif data == "dex_toggle_boost":
            from bot.handlers.launch import handle_dex_toggle
            await handle_dex_toggle(update, context, "boost")

        elif data == "dex_confirm":
            from bot.handlers.launch import handle_deploy_confirm
            await handle_deploy_confirm(update, context)

        elif data == "wallet_refresh":
            from bot.handlers.wallet_handler import show_wallet_reply
            await show_wallet_reply(query)

        elif data.startswith("panel_"):
            from bot.handlers.panel import handle_panel_callback
            await handle_panel_callback(update, context)

        else:
            logger.warning(f"Unknown callback data: {data}")

    except Exception as e:
        logger.error(f"Callback handler error: {e}", exc_info=True)
        try:
            await query.edit_message_text(
                error_message("An error occurred. Please try again or use /reset."),
                parse_mode="HTML",
            )
        except Exception:
            pass


async def _handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict, step: str) -> None:
    if step in ("withdraw_address", "withdraw_amount", "withdraw_confirm",
                "panel_transfer_address", "panel_transfer_amount"):
        session["step"] = "idle"
        await update.effective_message.reply_text(
            "Cancelled.",
            reply_markup=main_menu_keyboard(),
        )
    elif step == "collecting_optional":
        idx = session.get("optional_index", 0)
        if idx > 0:
            session["optional_index"] = idx - 1
            from bot.session import OPTIONAL_FIELDS, OPTIONAL_PROMPTS
            from bot.keyboards import optional_skip_keyboard
            field = OPTIONAL_FIELDS[idx - 1]
            await update.effective_message.reply_text(
                OPTIONAL_PROMPTS[field],
                parse_mode="HTML",
                reply_markup=optional_skip_keyboard(),
            )
        else:
            session["step"] = "collecting_required"
            session["required_index"] = 0
            from bot.session import REQUIRED_PROMPTS, REQUIRED_FIELDS
            await update.effective_message.reply_text(
                REQUIRED_PROMPTS[REQUIRED_FIELDS[0]],
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(),
            )
    else:
        await update.effective_message.reply_text(
            "Nothing to go back to.",
            reply_markup=main_menu_keyboard(),
        )
