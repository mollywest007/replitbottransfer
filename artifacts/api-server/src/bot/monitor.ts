import type { Telegraf, Context } from "telegraf";
import { getWalletBalance, getDeploymentWallet } from "./solana";
import { logger } from "../lib/logger";

const POLL_INTERVAL_MS = 30_000; // 30 seconds

interface BotContext extends Context {
  session: unknown;
}

class DepositMonitor {
  private subscribers = new Set<number>();
  private lastBalance: number | null = null;
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private bot: Telegraf<BotContext> | null = null;

  subscribe(chatId: number) {
    this.subscribers.add(chatId);
  }

  start(bot: Telegraf<BotContext>) {
    this.bot = bot;
    if (this.intervalId) return; // already running

    this.intervalId = setInterval(async () => {
      await this.poll();
    }, POLL_INTERVAL_MS);

    logger.info({ intervalMs: POLL_INTERVAL_MS }, "Deposit monitor started");
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  private async poll() {
    if (this.subscribers.size === 0) return;

    const wallet = getDeploymentWallet();
    if (!wallet) return;

    let currentBalance: number;
    try {
      currentBalance = await getWalletBalance(wallet);
    } catch {
      // RPC hiccup — skip this round
      return;
    }

    if (this.lastBalance === null) {
      // First reading — just set baseline, don't notify
      this.lastBalance = currentBalance;
      return;
    }

    const deposited = currentBalance - this.lastBalance;
    if (deposited > 0.000_01) {
      // Balance increased — notify all subscribers
      const message =
        `💰 *Deposit Received*\n\n` +
        `*Amount:* \`+${deposited.toFixed(4)} SOL\`\n` +
        `*New Balance:* \`${currentBalance.toFixed(4)} SOL\`\n` +
        `*Wallet:* \`${wallet}\`\n\n` +
        (currentBalance >= 5
          ? `✅ You have enough SOL to launch a token \\(/launch\\)\\.`
          : `⚠️ You need at least *5 SOL* to launch a token\\. ` +
            `Current balance: \`${currentBalance.toFixed(4)} SOL\`\\.`);

      if (this.bot) {
        for (const chatId of this.subscribers) {
          try {
            await this.bot.telegram.sendMessage(chatId, message, {
              parse_mode: "MarkdownV2",
            });
          } catch (err) {
            logger.warn({ err, chatId }, "Failed to notify subscriber of deposit");
            // Remove subscribers that have blocked the bot
            if (
              err instanceof Error &&
              (err.message.includes("bot was blocked") ||
                err.message.includes("chat not found"))
            ) {
              this.subscribers.delete(chatId);
            }
          }
        }
      }
    }

    this.lastBalance = currentBalance;
  }
}

// Singleton
export const depositMonitor = new DepositMonitor();
