import { Telegraf, session, Context } from "telegraf";
import type { SessionData, HistoryEntry } from "./session";
import { defaultSession } from "./session";
import {
  mainMenuMessage,
  helpMessage,
  reviewMessage,
  successMessage,
  errorMessage,
  insufficientFundsMessage,
  walletMessage,
  generatedWalletMessage,
  withdrawReviewMessage,
  withdrawSuccessMessage,
  DEPLOYMENT_FEE,
} from "./messages";
import {
  mainMenuKeyboard,
  yesNoKeyboard,
  backKeyboard,
  optionalSkipKeyboard,
  withdrawInputKeyboard,
  withdrawConfirmKeyboard,
  authorityInlineKeyboard,
} from "./keyboards";
import {
  deployToken,
  getDeploymentWallet,
  getWalletBalance,
  withdrawSol,
  generateNewWallet,
} from "./solana";
import { logger } from "../lib/logger";

interface BotContext extends Context {
  session: SessionData;
}

const REQUIRED_FIELDS: Array<keyof SessionData["token"]> = [
  "name",
  "symbol",
  "supply",
  "decimals",
];

const REQUIRED_PROMPTS: Record<string, string> = {
  name: "What is your *token name*?\n\nExample: `Solana Gold`",
  symbol: "What is your *token symbol*?\n\nExample: `SGOLD` (2–10 characters, uppercase)",
  supply: "What is the *total supply*?\n\nExample: `1000000000` (1 billion)",
  decimals: "How many *decimals*? (0–9)\n\nDefault is `9`. Send a number or type `skip` for default.",
};

const OPTIONAL_FIELDS: Array<keyof SessionData["token"]> = [
  "description",
  "logoUrl",
  "website",
  "telegram",
  "twitter",
];

const OPTIONAL_PROMPTS: Record<string, string> = {
  description: "*Token Description* (optional)\n\nSend a short description or tap *Skip*.",
  logoUrl: "*Token Logo* (optional)\n\nSend an image directly *or* paste a URL (https://...). Tap *Skip* to continue without a logo.",
  website: "*Website URL* (optional)\n\nSend your website or tap *Skip*.",
  telegram: "*Telegram Link* (optional)\n\nExample: `https://t.me/yourgroup` or tap *Skip*.",
  twitter: "*Twitter/X Link* (optional)\n\nExample: `https://x.com/yourhandle` or tap *Skip*.",
};

// ── History helpers ────────────────────────────────────────────────────────────

function pushHistory(ctx: BotContext) {
  const entry: HistoryEntry = {
    step: ctx.session.step,
    collectingField: ctx.session.collectingField,
  };
  ctx.session.history.push(entry);
}

export function createBot(token: string): Telegraf<BotContext> {
  const bot = new Telegraf<BotContext>(token);

  bot.use(session({ defaultSession }));

  // ── Back button ─────────────────────────────────────────────────────────────
  bot.hears("◀ Back", async (ctx) => {
    const entry = ctx.session.history.pop();
    if (!entry) {
      await ctx.replyWithMarkdown(
        "You're at the beginning.",
        mainMenuKeyboard()
      );
      return;
    }

    ctx.session.step = entry.step;
    ctx.session.collectingField = entry.collectingField;

    // Re-show the appropriate prompt for where they're going back to
    if (entry.step === "collecting_required" && entry.collectingField) {
      const isFirst = entry.collectingField === "name";
      const prompt = REQUIRED_PROMPTS[entry.collectingField]!;
      await ctx.replyWithMarkdown(
        prompt,
        isFirst ? undefined : backKeyboard()
      );
    } else if (entry.step === "collecting_optional" && entry.collectingField) {
      const isFirst = entry.collectingField === OPTIONAL_FIELDS[0];
      const prompt = OPTIONAL_PROMPTS[entry.collectingField]!;
      if (isFirst) {
        await ctx.replyWithMarkdown(
          "*Optional Details*\n\nTap *Skip* to skip any field, or *Done with optional fields* to move on.\n\n" + prompt,
          optionalSkipKeyboard()
        );
      } else {
        await ctx.replyWithMarkdown(prompt, optionalSkipKeyboard());
      }
    } else if (entry.step === "withdraw_address") {
      await ctx.replyWithMarkdown(
        "*Withdraw SOL*\n\nSend the recipient Solana wallet address.",
        withdrawInputKeyboard()
      );
    } else if (entry.step === "withdraw_amount") {
      await ctx.replyWithMarkdown(
        `*How much SOL to withdraw?*\n\nEnter an amount (e.g. \`1.5\`).`,
        withdrawInputKeyboard()
      );
    } else if (entry.step === "withdraw_confirm") {
      const { toAddress, amount } = ctx.session.withdraw;
      if (toAddress && amount) {
        const balance = await getWalletBalance(getDeploymentWallet());
        await ctx.replyWithMarkdown(
          withdrawReviewMessage(toAddress, amount, balance),
          withdrawConfirmKeyboard()
        );
      }
    } else {
      await ctx.replyWithMarkdown(mainMenuMessage(), mainMenuKeyboard());
    }
  });

  // ── Start / Main Menu ──────────────────────────────────────────────────────
  bot.start(async (ctx) => {
    ctx.session = defaultSession();
    await ctx.replyWithMarkdown(mainMenuMessage(), mainMenuKeyboard());
  });

  bot.command("help", async (ctx) => {
    await ctx.replyWithMarkdown(helpMessage());
  });

  bot.hears("Help", async (ctx) => {
    await ctx.replyWithMarkdown(helpMessage());
  });

  bot.command("reset", async (ctx) => {
    ctx.session = defaultSession();
    await ctx.replyWithMarkdown(
      "Session cleared. Ready to start fresh.",
      mainMenuKeyboard()
    );
  });

  bot.hears("Reset", async (ctx) => {
    ctx.session = defaultSession();
    await ctx.replyWithMarkdown(
      "Session cleared. Ready to start fresh.",
      mainMenuKeyboard()
    );
  });

  // ── Wallet Info ────────────────────────────────────────────────────────────
  bot.command("wallet", (ctx) => showWallet(ctx));
  bot.hears("Wallet Info", (ctx) => showWallet(ctx));

  async function showWallet(ctx: BotContext) {
    const address = getDeploymentWallet();
    const keyConfigured = !!process.env["PRIVATE_KEY"];
    if (!address) {
      await ctx.replyWithMarkdown(
        "*Wallet not configured.*\n\nThe `WALLET_ADDRESS` environment variable is missing."
      );
      return;
    }
    try {
      const balance = await getWalletBalance(address);
      await ctx.replyWithMarkdown(
        walletMessage(address, balance, keyConfigured),
        mainMenuKeyboard()
      );
    } catch {
      await ctx.replyWithMarkdown(
        walletMessage(address, 0, keyConfigured) +
          "\n\n_Could not fetch live balance — RPC may be unavailable._",
        mainMenuKeyboard()
      );
    }
  }

  // ── Generate Wallet ────────────────────────────────────────────────────────
  bot.command("genwallett", (ctx) => genWallet(ctx));
  bot.hears("Generate Wallet", (ctx) => genWallet(ctx));

  async function genWallet(ctx: BotContext) {
    const wallet = generateNewWallet();
    await ctx.replyWithMarkdown(
      generatedWalletMessage(wallet.address, wallet.privateKey),
      mainMenuKeyboard()
    );
  }

  // ── Withdraw SOL ───────────────────────────────────────────────────────────
  bot.command("withdraw", (ctx) => startWithdraw(ctx));
  bot.hears("Withdraw SOL", (ctx) => startWithdraw(ctx));

  async function startWithdraw(ctx: BotContext) {
    ctx.session.step = "withdraw_address";
    ctx.session.withdraw = {};
    ctx.session.history = [];
    await ctx.replyWithMarkdown(
      `*Withdraw SOL*\n\nSend the recipient Solana wallet address.`,
      withdrawInputKeyboard()
    );
  }

  bot.hears("Confirm Withdrawal", async (ctx) => {
    if (ctx.session.step !== "withdraw_confirm") {
      await ctx.replyWithMarkdown("Use /withdraw to start a withdrawal.");
      return;
    }

    const { toAddress, amount } = ctx.session.withdraw;
    if (!toAddress || !amount) {
      await ctx.replyWithMarkdown("Withdrawal data missing. Use /withdraw to try again.");
      return;
    }

    ctx.session.step = "idle";
    ctx.session.history = [];
    await ctx.replyWithMarkdown(`Sending \`${amount} SOL\`...`);

    try {
      const signature = await withdrawSol(toAddress, amount);
      await ctx.replyWithMarkdown(
        withdrawSuccessMessage(toAddress, amount, signature),
        mainMenuKeyboard()
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      logger.error({ err }, "Withdrawal failed");
      await ctx.replyWithMarkdown(
        `*Withdrawal Failed*\n\n${msg}\n\nUse /withdraw to try again.`,
        mainMenuKeyboard()
      );
    }
  });

  // ── Create Token ───────────────────────────────────────────────────────────
  bot.command("create", (ctx) => startCreate(ctx));
  bot.hears("Create Token", (ctx) => startCreate(ctx));

  async function startCreate(ctx: BotContext) {
    ctx.session = defaultSession();
    ctx.session.step = "collecting_required";
    ctx.session.collectingField = "name";
    await ctx.replyWithMarkdown(
      "*Create Token*\n\nLet's collect the required details.\n\n" +
        REQUIRED_PROMPTS["name"]!
    );
  }

  // ── Review ─────────────────────────────────────────────────────────────────
  bot.command("review", (ctx) => showReview(ctx));
  bot.hears("Review Deployment", (ctx) => showReview(ctx));

  async function showReview(ctx: BotContext) {
    const t = ctx.session.token;
    if (!t.name || !t.symbol || !t.supply || t.decimals === undefined) {
      await ctx.replyWithMarkdown(
        "Please complete token creation first.\n\nUse /create to begin."
      );
      return;
    }
    const wallet = getDeploymentWallet();
    await ctx.replyWithMarkdown(
      reviewMessage(t, wallet, DEPLOYMENT_FEE),
      mainMenuKeyboard()
    );
  }

  // ── Launch ─────────────────────────────────────────────────────────────────
  bot.command("launch", (ctx) => initiateLaunch(ctx));
  bot.hears("Launch Token", (ctx) => initiateLaunch(ctx));

  async function initiateLaunch(ctx: BotContext) {
    const t = ctx.session.token;
    if (!t.name || !t.symbol || !t.supply || t.decimals === undefined) {
      await ctx.replyWithMarkdown(
        "Token configuration is incomplete.\n\nUse /create to set up your token first."
      );
      return;
    }

    if (ctx.session.step === "deploying") {
      await ctx.replyWithMarkdown("Deployment is already in progress. Please wait.");
      return;
    }

    const wallet = getDeploymentWallet();
    const balance = await getWalletBalance(wallet);

    if (balance < DEPLOYMENT_FEE + 0.05) {
      await ctx.replyWithMarkdown(
        insufficientFundsMessage(balance, DEPLOYMENT_FEE)
      );
      return;
    }

    await ctx.replyWithMarkdown(
      reviewMessage(t, wallet, DEPLOYMENT_FEE) +
        "\n\n*Confirm deployment?*",
      yesNoKeyboard()
    );
    ctx.session.step = "review";
  }

  bot.hears("Yes, Launch", async (ctx) => {
    if (ctx.session.step !== "review") {
      await ctx.replyWithMarkdown("Please use /launch to start deployment.");
      return;
    }

    ctx.session.step = "deploying";
    await ctx.replyWithMarkdown(
      `*Deploying Token*\n\nSigning and broadcasting to Solana Mainnet...\n\nThis may take 30–60 seconds.`
    );

    try {
      const result = await deployToken(ctx.session.token, DEPLOYMENT_FEE);
      ctx.session.step = "done";
      ctx.session.history = [];
      await ctx.replyWithMarkdown(
        successMessage(
          result.mintAddress,
          result.txSignature,
          result.solscanUrl,
          result.timestamp
        ),
        mainMenuKeyboard()
      );
    } catch (err) {
      ctx.session.step = "idle";
      const msg = err instanceof Error ? err.message : String(err);
      logger.error({ err }, "Token deployment failed");
      await ctx.replyWithMarkdown(errorMessage(msg), mainMenuKeyboard());
    }
  });

  bot.hears("Cancel", async (ctx) => {
    ctx.session.step = "idle";
    ctx.session.history = [];
    await ctx.replyWithMarkdown("Cancelled.", mainMenuKeyboard());
  });

  // ── Optional fields ────────────────────────────────────────────────────────
  bot.hears("Done with optional fields", async (ctx) => {
    if (ctx.session.step !== "collecting_optional") return;
    pushHistory(ctx);
    ctx.session.step = "idle";
    await showAuthoritySettings(ctx);
  });

  bot.hears("Skip", async (ctx) => {
    if (ctx.session.step !== "collecting_optional") return;
    pushHistory(ctx);
    await advanceOptional(ctx);
  });

  // ── Authority toggles (inline) ─────────────────────────────────────────────
  bot.action("toggle_mint", async (ctx) => {
    ctx.session.token.revokeMint = !ctx.session.token.revokeMint;
    await ctx.editMessageReplyMarkup(
      authorityInlineKeyboard(
        ctx.session.token.revokeMint!,
        ctx.session.token.revokeFreeze!
      ).reply_markup
    );
    await ctx.answerCbQuery();
  });

  bot.action("toggle_freeze", async (ctx) => {
    ctx.session.token.revokeFreeze = !ctx.session.token.revokeFreeze;
    await ctx.editMessageReplyMarkup(
      authorityInlineKeyboard(
        ctx.session.token.revokeMint!,
        ctx.session.token.revokeFreeze!
      ).reply_markup
    );
    await ctx.answerCbQuery();
  });

  bot.action("authority_done", async (ctx) => {
    ctx.session.step = "idle";
    ctx.session.history = [];
    await ctx.answerCbQuery("Settings saved");
    const wallet = getDeploymentWallet();
    await ctx.replyWithMarkdown(
      reviewMessage(ctx.session.token, wallet, DEPLOYMENT_FEE) +
        "\n\nUse /launch when ready.",
      mainMenuKeyboard()
    );
  });

  // ── Photo upload handler ───────────────────────────────────────────────────
  bot.on("photo", async (ctx) => {
    if (
      ctx.session.step !== "collecting_optional" ||
      ctx.session.collectingField !== "logoUrl"
    ) {
      await ctx.replyWithMarkdown(
        "I can only accept images during the logo step.\n\nUse /create to start token setup."
      );
      return;
    }

    const photos = ctx.message.photo;
    const best = photos[photos.length - 1]!;
    try {
      const fileLink = await ctx.telegram.getFileLink(best.file_id);
      ctx.session.token.logoUrl = fileLink.href;
      await ctx.replyWithMarkdown("Logo uploaded.");
      pushHistory(ctx);
      await advanceOptional(ctx);
    } catch (err) {
      logger.error({ err }, "Failed to get file link for photo");
      await ctx.replyWithMarkdown(
        "Could not process the image. Please try again or paste a URL instead."
      );
    }
  });

  // ── Document upload handler (images sent as files) ─────────────────────────
  bot.on("document", async (ctx) => {
    if (
      ctx.session.step !== "collecting_optional" ||
      ctx.session.collectingField !== "logoUrl"
    ) {
      await ctx.replyWithMarkdown(
        "I can only accept images during the logo step.\n\nUse /create to start token setup."
      );
      return;
    }

    const doc = ctx.message.document;
    if (!doc.mime_type?.startsWith("image/")) {
      await ctx.replyWithMarkdown(
        "Please send an image file (PNG, JPG, etc.) or a URL."
      );
      return;
    }

    try {
      const fileLink = await ctx.telegram.getFileLink(doc.file_id);
      ctx.session.token.logoUrl = fileLink.href;
      await ctx.replyWithMarkdown("Logo uploaded.");
      pushHistory(ctx);
      await advanceOptional(ctx);
    } catch (err) {
      logger.error({ err }, "Failed to get file link for document");
      await ctx.replyWithMarkdown(
        "Could not process the image. Please try again or paste a URL instead."
      );
    }
  });

  // ── General message handler (step machine) ─────────────────────────────────
  bot.on("text", async (ctx) => {
    const text = ctx.message.text.trim();

    if (ctx.session.step === "collecting_required") {
      await handleRequiredInput(ctx, text);
      return;
    }

    if (ctx.session.step === "collecting_optional") {
      await handleOptionalInput(ctx, text);
      return;
    }

    if (ctx.session.step === "withdraw_address") {
      await handleWithdrawAddress(ctx, text);
      return;
    }

    if (ctx.session.step === "withdraw_amount") {
      await handleWithdrawAmount(ctx, text);
      return;
    }

    // Fallback
    await ctx.replyWithMarkdown(mainMenuMessage(), mainMenuKeyboard());
  });

  return bot;
}

// ── Step helpers ──────────────────────────────────────────────────────────────

async function handleRequiredInput(ctx: BotContext, text: string) {
  const field = ctx.session.collectingField as keyof SessionData["token"];

  if (field === "name") {
    if (text.length < 1 || text.length > 50) {
      await ctx.replyWithMarkdown("Token name must be 1–50 characters. Try again.");
      return;
    }
    ctx.session.token.name = text;
  } else if (field === "symbol") {
    const sym = text.toUpperCase().replace(/\s/g, "");
    if (sym.length < 2 || sym.length > 10) {
      await ctx.replyWithMarkdown("Symbol must be 2–10 characters. Try again.");
      return;
    }
    ctx.session.token.symbol = sym;
  } else if (field === "supply") {
    const num = Number(text.replace(/[,_]/g, ""));
    if (isNaN(num) || num <= 0 || num > 1e18) {
      await ctx.replyWithMarkdown(
        "Invalid supply. Enter a positive number (e.g. `1000000000`)."
      );
      return;
    }
    ctx.session.token.supply = num;
  } else if (field === "decimals") {
    if (text.toLowerCase() === "skip") {
      ctx.session.token.decimals = 9;
    } else {
      const d = parseInt(text, 10);
      if (isNaN(d) || d < 0 || d > 9) {
        await ctx.replyWithMarkdown("Decimals must be 0–9. Try again.");
        return;
      }
      ctx.session.token.decimals = d;
    }
  }

  pushHistory(ctx);
  await advanceRequired(ctx);
}

async function advanceRequired(ctx: BotContext) {
  const currentIndex = REQUIRED_FIELDS.indexOf(
    ctx.session.collectingField as keyof SessionData["token"]
  );
  const next = REQUIRED_FIELDS[currentIndex + 1];

  if (next) {
    ctx.session.collectingField = next;
    await ctx.replyWithMarkdown(REQUIRED_PROMPTS[next]!, backKeyboard());
  } else {
    // Move to optional
    ctx.session.step = "collecting_optional";
    ctx.session.collectingField = OPTIONAL_FIELDS[0];
    await ctx.replyWithMarkdown(
      "*Optional Details*\n\nTap *Skip* to skip any field, or *Done with optional fields* to move on.\n\n" +
        OPTIONAL_PROMPTS[OPTIONAL_FIELDS[0]!]!,
      optionalSkipKeyboard()
    );
  }
}

async function handleOptionalInput(ctx: BotContext, text: string) {
  const field = ctx.session.collectingField as keyof SessionData["token"];

  if (field === "logoUrl" || field === "website" || field === "telegram" || field === "twitter") {
    if (!text.startsWith("http://") && !text.startsWith("https://")) {
      await ctx.replyWithMarkdown(
        "Please send a valid URL starting with `https://`, or tap *Skip*."
      );
      return;
    }
  }

  (ctx.session.token as Record<string, unknown>)[field] = text;
  pushHistory(ctx);
  await advanceOptional(ctx);
}

async function advanceOptional(ctx: BotContext) {
  const currentIndex = OPTIONAL_FIELDS.indexOf(
    ctx.session.collectingField as keyof SessionData["token"]
  );
  const next = OPTIONAL_FIELDS[currentIndex + 1];

  if (next) {
    ctx.session.collectingField = next;
    await ctx.replyWithMarkdown(OPTIONAL_PROMPTS[next]!, optionalSkipKeyboard());
  } else {
    await showAuthoritySettings(ctx);
  }
}

async function showAuthoritySettings(ctx: BotContext) {
  ctx.session.step = "idle";
  await ctx.replyWithMarkdown(
    "*Authority Settings*\n\nConfigure mint and freeze authority.\nRevoking makes the token immutable.",
    authorityInlineKeyboard(
      ctx.session.token.revokeMint!,
      ctx.session.token.revokeFreeze!
    )
  );
}

// ── Withdrawal helpers ────────────────────────────────────────────────────────

function isValidSolanaAddress(address: string): boolean {
  return /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(address);
}

async function handleWithdrawAddress(ctx: BotContext, text: string) {
  if (!isValidSolanaAddress(text)) {
    await ctx.replyWithMarkdown(
      "That doesn't look like a valid Solana address. Please try again."
    );
    return;
  }
  pushHistory(ctx);
  ctx.session.withdraw.toAddress = text;
  ctx.session.step = "withdraw_amount";
  await ctx.replyWithMarkdown(
    `*How much SOL to withdraw?*\n\nEnter an amount (e.g. \`1.5\`).`,
    withdrawInputKeyboard()
  );
}

async function handleWithdrawAmount(ctx: BotContext, text: string) {
  const amount = parseFloat(text);
  if (isNaN(amount) || amount <= 0) {
    await ctx.replyWithMarkdown(
      "Invalid amount. Enter a positive number (e.g. `1.5`)."
    );
    return;
  }

  const walletAddress = getDeploymentWallet();
  let balance = 0;
  try {
    balance = await getWalletBalance(walletAddress);
  } catch {
    await ctx.replyWithMarkdown(
      "Could not fetch wallet balance. Please try again."
    );
    return;
  }

  if (amount + 0.01 > balance) {
    await ctx.replyWithMarkdown(
      `*Insufficient balance.*\n\nAvailable: \`${balance.toFixed(4)} SOL\`\nRequested: \`${amount} SOL\`\n\nReduce the amount and try again.`
    );
    return;
  }

  pushHistory(ctx);
  ctx.session.withdraw.amount = amount;
  ctx.session.step = "withdraw_confirm";

  await ctx.replyWithMarkdown(
    withdrawReviewMessage(ctx.session.withdraw.toAddress!, amount, balance),
    withdrawConfirmKeyboard()
  );
}
