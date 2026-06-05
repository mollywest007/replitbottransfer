"""Token creation flow — collects required and optional fields step by step."""
from telegram import Update
from telegram.ext import ContextTypes
from bot.session import (
    get_session, REQUIRED_FIELDS, REQUIRED_PROMPTS,
    OPTIONAL_FIELDS, OPTIONAL_PROMPTS,
)
from bot.keyboards import main_menu_keyboard, optional_skip_keyboard, authority_inline_keyboard
from utils.logger import logger


async def start_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    session["step"] = "collecting_required"
    session["required_index"] = 0
    session["optional_index"] = 0
    session["token"]["name"] = None
    session["token"]["symbol"] = None
    session["token"]["description"] = None
    session["token"]["logo_url"] = None
    session["token"]["website"] = None
    session["token"]["telegram"] = None
    session["token"]["twitter"] = None
    session["token"]["revoke_mint"] = False
    session["token"]["revoke_freeze"] = False

    first_field = REQUIRED_FIELDS[0]
    await update.message.reply_text(
        f"<b>Create Token</b>\n\n{REQUIRED_PROMPTS[first_field]}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def handle_required_field(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    session = get_session(context)
    idx = session.get("required_index", 0)
    field = REQUIRED_FIELDS[idx]

    if field == "symbol":
        text = text.upper().strip()
        if len(text) < 2 or len(text) > 10:
            await update.message.reply_text(
                "Symbol must be 2–10 characters. Please try again.",
            )
            return

    session["token"][field] = text
    idx += 1
    session["required_index"] = idx

    if idx < len(REQUIRED_FIELDS):
        next_field = REQUIRED_FIELDS[idx]
        await update.message.reply_text(
            REQUIRED_PROMPTS[next_field],
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await _start_optional_fields(update, context)


async def _start_optional_fields(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    session["step"] = "collecting_optional"
    session["optional_index"] = 0
    field = OPTIONAL_FIELDS[0]
    await update.message.reply_text(
        f"<b>Optional Details</b>\n\n{OPTIONAL_PROMPTS[field]}",
        parse_mode="HTML",
        reply_markup=optional_skip_keyboard(),
    )


async def handle_optional_field(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    session = get_session(context)
    idx = session.get("optional_index", 0)
    field = OPTIONAL_FIELDS[idx]
    session["token"][field] = text
    await _advance_optional(update, context)


async def handle_optional_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    if session.get("step") != "collecting_optional":
        return
    idx = session.get("optional_index", 0)
    field = OPTIONAL_FIELDS[idx]
    if field != "logo_url":
        return

    photo = update.message.photo[-1]
    try:
        file = await photo.get_file()
        session["token"]["logo_url"] = file.file_path
        await _advance_optional(update, context)
    except Exception as e:
        logger.warning(f"Failed to get photo file: {e}")
        await update.message.reply_text(
            "Could not process photo. Please send a direct image URL instead.",
        )


async def skip_optional(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _advance_optional(update, context)


async def _advance_optional(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    idx = session.get("optional_index", 0) + 1
    session["optional_index"] = idx

    if idx < len(OPTIONAL_FIELDS):
        field = OPTIONAL_FIELDS[idx]
        await update.message.reply_text(
            OPTIONAL_PROMPTS[field],
            parse_mode="HTML",
            reply_markup=optional_skip_keyboard(),
        )
    else:
        await show_authority_settings(update, context)


async def show_authority_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session(context)
    session["step"] = "authority"
    token = session["token"]
    await update.message.reply_text(
        "<b>Authority Settings</b>\n\n"
        "Choose which authorities to revoke at launch.\n"
        "Revoking makes your token more trustworthy to buyers.\n\n"
        "Tap <b>Done</b> when finished.",
        parse_mode="HTML",
        reply_markup=authority_inline_keyboard(
            token.get("revoke_mint", False),
            token.get("revoke_freeze", False),
        ),
    )
