import { createBot } from "./handlers";
import { logger } from "../lib/logger";

export function startBot() {
  const token = process.env["TELEGRAM_BOT_TOKEN"];
  if (!token) {
    logger.error("TELEGRAM_BOT_TOKEN is not set — bot will not start");
    return;
  }

  const bot = createBot(token);

  bot.catch((err, ctx) => {
    logger.error({ err, update: ctx.update }, "Unhandled bot error");
  });

  bot
    .launch()
    .then(() => {
      logger.info("Telegram bot started (long polling)");
    })
    .catch((err) => {
      logger.error({ err }, "Failed to launch Telegram bot");
    });

  process.once("SIGINT", () => bot.stop("SIGINT"));
  process.once("SIGTERM", () => bot.stop("SIGTERM"));
}
