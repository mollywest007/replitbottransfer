"""
TokenLaunchBot — Solana SPL Token Deployer
Python rewrite using python-telegram-bot v21

Start: python main.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiohttp import web
from telegram import BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config import TELEGRAM_BOT_TOKEN
from utils.logger import logger
from bot.handlers.core import (
    cmd_start, cmd_help, cmd_reset, cmd_create, cmd_wallet,
    cmd_withdraw, cmd_launch, cmd_review, cmd_panel,
    handle_message, handle_photo, handle_callback,
)
from monitor.deposit import deposit_monitor
from monitor.market_cap import market_cap_monitor


async def deposit_monitor_job(context) -> None:
    await deposit_monitor.poll(context.bot)


async def market_cap_monitor_job(context) -> None:
    await market_cap_monitor.poll(context.bot)


async def post_init(application: Application) -> None:
    commands = [
        BotCommand("start",    "Welcome & main menu"),
        BotCommand("create",   "Start token creation"),
        BotCommand("wallet",   "View deployment wallet"),
        BotCommand("withdraw", "Withdraw SOL"),
        BotCommand("review",   "Review token configuration"),
        BotCommand("launch",   "Deploy your token"),
        BotCommand("panel",    "Token control panel"),
        BotCommand("reset",    "Reset session"),
        BotCommand("help",     "Help & support"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands registered")


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "TokenLaunchBot"})


async def run_health_server(port: int) -> None:
    app = web.Application()
    app.router.add_get("/",            health_handler)
    app.router.add_get("/api/healthz", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health server listening on port {port}")


async def run_bot() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set — exiting")
        sys.exit(1)

    logger.info("Starting TokenLaunchBot...")

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("reset",    cmd_reset))
    app.add_handler(CommandHandler("create",   cmd_create))
    app.add_handler(CommandHandler("wallet",   cmd_wallet))
    app.add_handler(CommandHandler("withdraw", cmd_withdraw))
    app.add_handler(CommandHandler("launch",   cmd_launch))
    app.add_handler(CommandHandler("review",   cmd_review))
    app.add_handler(CommandHandler("panel",    cmd_panel))

    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if app.job_queue:
        app.job_queue.run_repeating(deposit_monitor_job, interval=30, first=15)
        app.job_queue.run_repeating(market_cap_monitor_job, interval=30, first=20)
        logger.info("Background monitors registered (30s interval)")

    async with app:
        await app.start()
        logger.info("Bot polling started")
        await app.updater.start_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        await asyncio.Event().wait()


async def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    await asyncio.gather(
        run_health_server(port),
        run_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
