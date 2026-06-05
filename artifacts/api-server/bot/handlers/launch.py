"""Launch flow — launchpad select → creator buy → target mcap → DEX options → deploy."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.session import get_session
from bot.keyboards import (
    main_menu_keyboard, launchpad_keyboard, creator_buy_keyboard,
    target_mcap_keyboard, dex_options_keyboard,
)
from bot.messages import (
    launchpad_select_message, creator_buy_message, target_mcap_message,
    dex_options_message, deploying_message, insufficient_funds_message,
    pumpfun_success_message, raydium_success_message, error_message,
)
from pricing.dex import fetch_dex_prices
from solana_client.wallet import get_wallet_address, get_wallet_balance
from config import DEPLOYMENT_FEE, PLATFORM_FEE_USD, CREATION_BUFFER_SOL
from monitor.deposit import deposit_monitor
from monitor.market_cap import market_cap_monitor
from utils.logger import logger


async def initiate_launch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    token = session["token"]

    if not token.get("name") or not token.get("symbol"):
        await update.message.reply_text(
            "Please complete token creation first. Use /create to start.",
            reply_markup=main_menu_keyboard(),
        )
        return

    session["step"] = "select_launchpad"
    await update.message.reply_text(
        launchpad_select_message(token["name"], token["symbol"]),
        parse_mode="HTML",
        reply_markup=launchpad_keyboard(),
    )


async def handle_launchpad_selected(update: Update, context: ContextTypes.DEFAULT_TYPE, launchpad: str) -> None:
    session = get_session(context)
    session["launchpad"] = launchpad
    session["step"] = "creator_buy"

    wallet = get_wallet_address()
    balance = await get_wallet_balance(wallet)

    query = update.callback_query
    await query.edit_message_text(
        creator_buy_message(launchpad, balance),
        parse_mode="HTML",
        reply_markup=creator_buy_keyboard(),
    )


async def handle_creator_buy_selected(update: Update, context: ContextTypes.DEFAULT_TYPE, value: str) -> None:
    session = get_session(context)
    query = update.callback_query

    if value == "skip":
        session["creator_buy_amount_sol"] = 0.0
        await _show_target_mcap(update, context)
    elif value == "custom":
        session["step"] = "creator_buy_custom"
        await query.edit_message_text(
            "Enter the amount of SOL you want to invest as creator.\n\nExample: <code>1.5</code>",
            parse_mode="HTML",
        )
    else:
        session["creator_buy_amount_sol"] = float(value)
        await _show_target_mcap(update, context)


async def handle_creator_buy_custom_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    session = get_session(context)
    try:
        amount = float(text.strip())
        if amount < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "Invalid amount. Please enter a positive number like 1.5.",
        )
        return

    session["creator_buy_amount_sol"] = amount
    session["step"] = "target_mcap"
    await update.message.reply_text(
        target_mcap_message(amount),
        parse_mode="HTML",
        reply_markup=target_mcap_keyboard(),
    )


async def _show_target_mcap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    session["step"] = "target_mcap"
    query = update.callback_query
    await query.edit_message_text(
        target_mcap_message(session.get("creator_buy_amount_sol", 0.0)),
        parse_mode="HTML",
        reply_markup=target_mcap_keyboard(),
    )


async def handle_target_mcap_selected(update: Update, context: ContextTypes.DEFAULT_TYPE, value: str) -> None:
    session = get_session(context)
    query = update.callback_query

    if value == "skip":
        session["target_market_cap_usd"] = 0.0
        await _show_dex_options(update, context)
    elif value == "custom":
        session["step"] = "target_mcap_custom"
        await query.edit_message_text(
            "Enter your target market cap in USD.\n\nExample: <code>250000</code>",
            parse_mode="HTML",
        )
    else:
        session["target_market_cap_usd"] = float(value)
        await _show_dex_options(update, context)


async def handle_target_mcap_custom_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    session = get_session(context)
    try:
        amount = float(text.strip().replace(",", "").replace("$", ""))
        if amount < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "Invalid amount. Please enter a positive number like 100000.",
        )
        return

    session["target_market_cap_usd"] = amount
    session["step"] = "dex_options"
    prices = await fetch_dex_prices()
    wallet = get_wallet_address()
    balance = await get_wallet_balance(wallet)
    await update.message.reply_text(
        dex_options_message(
            prices, balance,
            session.get("creator_buy_amount_sol", 0.0),
            amount,
            session.get("dex_update", False),
            session.get("dex_boost", False),
        ),
        parse_mode="HTML",
        reply_markup=dex_options_keyboard(prices, session.get("dex_update", False), session.get("dex_boost", False)),
    )


async def _show_dex_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    session["step"] = "dex_options"
    prices = await fetch_dex_prices()
    wallet = get_wallet_address()
    balance = await get_wallet_balance(wallet)
    query = update.callback_query
    await query.edit_message_text(
        dex_options_message(
            prices, balance,
            session.get("creator_buy_amount_sol", 0.0),
            session.get("target_market_cap_usd", 0.0),
            session.get("dex_update", False),
            session.get("dex_boost", False),
        ),
        parse_mode="HTML",
        reply_markup=dex_options_keyboard(prices, session.get("dex_update", False), session.get("dex_boost", False)),
    )


async def handle_dex_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE, option: str) -> None:
    session = get_session(context)
    if option == "update":
        session["dex_update"] = not session.get("dex_update", False)
    else:
        session["dex_boost"] = not session.get("dex_boost", False)
    await _show_dex_options(update, context)


async def handle_deploy_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    query = update.callback_query
    launchpad = session.get("launchpad", "pumpfun")
    creator_buy = session.get("creator_buy_amount_sol", 0.0)
    target_mcap = session.get("target_market_cap_usd", 0.0)
    dex_update = session.get("dex_update", False)
    dex_boost = session.get("dex_boost", False)
    token = session["token"]

    prices = await fetch_dex_prices()
    sol_usd = prices["sol_usd"]
    platform_sol = PLATFORM_FEE_USD / sol_usd
    dex_update_sol = prices["update_sol"] if dex_update else 0.0
    dex_boost_sol = prices["boost_sol"] if dex_boost else 0.0
    total_required = CREATION_BUFFER_SOL + platform_sol + creator_buy + dex_update_sol + dex_boost_sol

    wallet = get_wallet_address()
    balance = await get_wallet_balance(wallet)

    if balance < max(total_required, DEPLOYMENT_FEE):
        needed = max(total_required, DEPLOYMENT_FEE)
        await query.edit_message_text(
            insufficient_funds_message(balance, needed),
            parse_mode="HTML",
        )
        return

    session["step"] = "deploying"
    await query.edit_message_text(
        deploying_message(launchpad),
        parse_mode="HTML",
    )

    chat_id = update.effective_chat.id
    deposit_monitor.subscribe(chat_id)

    try:
        if launchpad == "pumpfun":
            from solana_client.launchpad import deploy_pumpfun
            result = await deploy_pumpfun(token, creator_buy)

            session["last_mint"] = result["mint_address"]
            session["last_symbol"] = token["symbol"]
            session["last_decimals"] = token.get("decimals", 6)
            session["step"] = "done"

            if target_mcap > 0:
                market_cap_monitor.add_target(
                    mint_address=result["mint_address"],
                    target_usd=target_mcap,
                    chat_id=chat_id,
                    symbol=token["symbol"],
                    launchpad="pumpfun",
                    wallet_address=wallet,
                )

            await context.bot.send_message(
                chat_id=chat_id,
                text=pumpfun_success_message(
                    result["mint_address"], result["tx_signature"],
                    result["view_url"], result["timestamp"],
                    creator_buy, target_mcap,
                ),
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(),
            )

        else:
            from solana_client.launchpad import deploy_raydium
            result = await deploy_raydium(token, creator_buy)

            session["last_mint"] = result["mint_address"]
            session["last_symbol"] = token["symbol"]
            session["last_decimals"] = token.get("decimals", 9)
            session["step"] = "done"

            if target_mcap > 0:
                market_cap_monitor.add_target(
                    mint_address=result["mint_address"],
                    target_usd=target_mcap,
                    chat_id=chat_id,
                    symbol=token["symbol"],
                    launchpad="raydium",
                    wallet_address=wallet,
                )

            await context.bot.send_message(
                chat_id=chat_id,
                text=raydium_success_message(
                    result["mint_address"], result["tx_signature"],
                    result["timestamp"], target_mcap,
                ),
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(),
            )

    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        session["step"] = "idle"
        await context.bot.send_message(
            chat_id=chat_id,
            text=error_message(f"Deployment failed: {str(e)[:200]}"),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
