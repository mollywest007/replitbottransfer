import { createBot } from "./handlers";
import { depositMonitor } from "./monitor";
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
      // Start deposit monitor after bot is up
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      depositMonitor.start(bot as any);
    })
    .catch((err) => {
      logger.error({ err }, "Failed to launch Telegram bot");
    });

  process.once("SIGINT", () => {
    depositMonitor.stop();
    bot.stop("SIGINT");
  });
  process.once("SIGTERM", () => {
    depositMonitor.stop();
    bot.stop("SIGTERM");
  });
}
