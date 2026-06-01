import type { Telegraf, Context } from "telegraf";
import { getWalletBalance, getDeploymentWallet } from "./solana";
import { autoSellExecutedMessage, autoSellNotifyMessage } from "./messages";
import { logger } from "../lib/logger";

const POLL_INTERVAL_MS = 30_000; // 30 seconds

interface BotContext extends Context {
  session: unknown;
}

// ── Deposit Monitor ───────────────────────────────────────────────────────────

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
    if (this.intervalId) return;

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
      return;
    }

    if (this.lastBalance === null) {
      this.lastBalance = currentBalance;
      return;
    }

    const deposited = currentBalance - this.lastBalance;
    if (deposited > 0.000_01) {
      const message =
        `💰 *Deposit Received*\n\n` +
        `*Amount:* \`+${deposited.toFixed(4)} SOL\`\n` +
        `*New Balance:* \`${currentBalance.toFixed(4)} SOL\`\n` +
        `*Wallet:* \`${wallet}\`\n\n` +
        (currentBalance >= 5
          ? `✅ You have enough SOL\\. Use /launch when your token is ready\\.`
          : `⚠️ Minimum 5 SOL required\\. Current: \`${currentBalance.toFixed(4)} SOL\`\\.`);

      if (this.bot) {
        for (const chatId of this.subscribers) {
          try {
            await this.bot.telegram.sendMessage(chatId, message, {
              parse_mode: "MarkdownV2",
            });
          } catch (err) {
            logger.warn({ err, chatId }, "Failed to notify subscriber of deposit");
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

// ── Market Cap Monitor ────────────────────────────────────────────────────────

interface McapJob {
  mintAddress: string;
  targetUsd: number;
  chatId: number;
  launchpad: "pumpfun" | "raydium";
  hasCreatorTokens: boolean;
}

class MarketCapMonitor {
  private jobs = new Map<string, McapJob>(); // key = mintAddress
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private bot: Telegraf<BotContext> | null = null;

  start(bot: Telegraf<BotContext>) {
    this.bot = bot;
    if (this.intervalId) return;

    this.intervalId = setInterval(async () => {
      await this.pollAll();
    }, POLL_INTERVAL_MS);

    logger.info("Market cap monitor started");
  }

  /** Register a token to watch. */
  watch(job: McapJob) {
    this.jobs.set(job.mintAddress, job);
    logger.info(
      { mint: job.mintAddress, targetUsd: job.targetUsd, launchpad: job.launchpad },
      "Market cap watch registered"
    );
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  private async pollAll() {
    for (const [mint, job] of this.jobs) {
      try {
        const mcap = await fetchMarketCap(mint, job.launchpad);
        if (mcap === null) continue;

        logger.info({ mint, mcap, target: job.targetUsd }, "Market cap polled");

        if (mcap >= job.targetUsd) {
          this.jobs.delete(mint); // stop watching first
          await this.triggerSell(job, mcap);
        }
      } catch (err) {
        logger.warn({ err, mint }, "Error polling market cap");
      }
    }
  }

  private async triggerSell(job: McapJob, currentMcapUsd: number) {
    if (!this.bot) return;

    if (job.launchpad === "pumpfun" && job.hasCreatorTokens) {
      // Attempt automatic sell via Pump.fun SDK
      try {
        const { sellAllPumpFun } = await import("./launchpad");
        const sellResult = await sellAllPumpFun(job.mintAddress);
        const msg = autoSellExecutedMessage(
          job.mintAddress,
          sellResult.txSignature,
          currentMcapUsd
        );
        await this.bot.telegram.sendMessage(job.chatId, msg, { parse_mode: "Markdown" });
      } catch (err) {
        logger.error({ err, mint: job.mintAddress }, "Auto-sell failed");
        // Fallback to notify-only
        const msg =
          autoSellNotifyMessage(job.mintAddress, currentMcapUsd) +
          `\n\n_Auto-sell encountered an error — please sell manually via Token Panel._`;
        await this.bot.telegram.sendMessage(job.chatId, msg, { parse_mode: "Markdown" });
      }
    } else {
      // Raydium or no creator tokens — notify user to sell manually
      const msg = autoSellNotifyMessage(job.mintAddress, currentMcapUsd);
      await this.bot.telegram.sendMessage(job.chatId, msg, { parse_mode: "Markdown" });
    }
  }
}

/** Fetch current market cap in USD from DEX Screener or Pump.fun API. */
async function fetchMarketCap(
  mintAddress: string,
  launchpad: "pumpfun" | "raydium"
): Promise<number | null> {
  // Try Pump.fun API first for pumpfun tokens (more accurate early on)
  if (launchpad === "pumpfun") {
    try {
      const res = await fetch(
        `https://frontend-api.pump.fun/coins/${mintAddress}`,
        { signal: AbortSignal.timeout(8_000) }
      );
      if (res.ok) {
        const data = (await res.json()) as { market_cap?: number; usd_market_cap?: number };
        const mcap = data.usd_market_cap ?? data.market_cap;
        if (mcap && mcap > 0) return mcap;
      }
    } catch {
      // fall through to DEX Screener
    }
  }

  // DEX Screener fallback (works for both launchpads once there's a pool)
  try {
    const res = await fetch(
      `https://api.dexscreener.com/latest/dex/tokens/${mintAddress}`,
      { signal: AbortSignal.timeout(8_000) }
    );
    if (!res.ok) return null;
    const data = (await res.json()) as {
      pairs?: { fdv?: number; marketCap?: number }[];
    };
    const pair = data.pairs?.[0];
    if (!pair) return null;
    return pair.marketCap ?? pair.fdv ?? null;
  } catch {
    return null;
  }
}

// Singletons
export const depositMonitor = new DepositMonitor();
export const marketCapMonitor = new MarketCapMonitor();
