import type { TokenConfig } from "./session";
import type { DexServicePrices } from "./dex-pricing";
import { fmtSolUsd } from "./dex-pricing";

/** Minimum SOL that must be in the wallet for the bot to operate. */
export const DEPLOYMENT_FEE = 5; // SOL

export function mainMenuMessage(): string {
  return (
    `*TokenLaunchBot* — Solana SPL Token Deployer\n\n` +
    `Deploy tokens on Solana in minutes.\n\n` +
    `*Commands*\n` +
    `/create — Start token creation\n` +
    `/wallet — Deployment wallet info\n` +
    `/withdraw — Withdraw SOL\n` +
    `/panel — Token control panel\n` +
    `/review — Review deployment details\n` +
    `/launch — Deploy your token\n` +
    `/reset — Start over\n` +
    `/help — Show help`
  );
}

export function walletMessage(
  address: string,
  balance: number,
  keyConfigured: boolean
): string {
  return (
    `*Deployment Wallet*\n\n` +
    `*Address*\n\`${address}\`\n\n` +
    `*Balance*\n\`${balance.toFixed(4)} SOL\`\n\n` +
    `*Minimum Required*\n\`${DEPLOYMENT_FEE} SOL\`\n\n` +
    `*Private Key*\n${keyConfigured ? "`Configured ✓`" : "`Not configured ✗`"}\n\n` +
    `*Network*\nSolana Mainnet\n\n` +
    `_This is a fixed deployment wallet. It cannot be changed._`
  );
}

export function panelMessage(
  mintAddress: string,
  symbol: string,
  uiBalance: number,
  decimals: number
): string {
  return (
    `*Token Control Panel*\n\n` +
    `*Token*\n\`${symbol}\`\n\n` +
    `*Mint*\n\`${mintAddress}\`\n\n` +
    `*Wallet Balance*\n\`${uiBalance.toLocaleString(undefined, { maximumFractionDigits: decimals })} ${symbol}\`\n\n` +
    `Choose an action:`
  );
}

export function burnConfirmMessage(
  symbol: string,
  uiAmount: number,
  portion: "half" | "all"
): string {
  return (
    `*Confirm Burn*\n\n` +
    `You are about to burn *${portion === "half" ? "half" : "all"}* of your ${symbol} tokens.\n\n` +
    `*Amount:* \`${uiAmount.toLocaleString()} ${symbol}\`\n\n` +
    `This is *irreversible.* The tokens will be permanently destroyed.`
  );
}

export function burnSuccessMessage(
  symbol: string,
  uiAmount: number,
  txSignature: string
): string {
  const shortTx = `${txSignature.slice(0, 8)}...${txSignature.slice(-8)}`;
  return (
    `*Tokens Burned*\n\n` +
    `*Amount:* \`${uiAmount.toLocaleString()} ${symbol}\`\n\n` +
    `*Transaction:* \`${shortTx}\`\n\n` +
    `*Status:* Confirmed`
  );
}

export function transferTokenReviewMessage(
  toAddress: string,
  uiAmount: number,
  symbol: string
): string {
  return (
    `*Transfer Review*\n\n` +
    `*To*\n\`${toAddress}\`\n\n` +
    `*Amount*\n\`${uiAmount.toLocaleString()} ${symbol}\`\n\n` +
    `Confirm to send.`
  );
}

export function transferTokenSuccessMessage(
  toAddress: string,
  uiAmount: number,
  symbol: string,
  txSignature: string
): string {
  const shortTx = `${txSignature.slice(0, 8)}...${txSignature.slice(-8)}`;
  return (
    `*Transfer Sent*\n\n` +
    `*To:* \`${toAddress}\`\n` +
    `*Amount:* \`${uiAmount.toLocaleString()} ${symbol}\`\n` +
    `*Transaction:* \`${shortTx}\`\n\n` +
    `*Status:* Confirmed`
  );
}

export function revokeConfirmMessage(
  type: "mint" | "freeze",
  symbol: string
): string {
  const label = type === "mint" ? "Mint Authority" : "Freeze Authority";
  const effect =
    type === "mint"
      ? "No more tokens can ever be minted."
      : "Token accounts can no longer be frozen.";
  return (
    `*Confirm Revoke ${label}*\n\n` +
    `Token: \`${symbol}\`\n\n` +
    `${effect}\n\n` +
    `This is *irreversible.*`
  );
}

export function revokeSuccessMessage(
  type: "mint" | "freeze",
  symbol: string,
  txSignature: string
): string {
  const label = type === "mint" ? "Mint Authority" : "Freeze Authority";
  const shortTx = `${txSignature.slice(0, 8)}...${txSignature.slice(-8)}`;
  return (
    `*${label} Revoked*\n\n` +
    `Token: \`${symbol}\`\n` +
    `*Transaction:* \`${shortTx}\`\n\n` +
    `*Status:* Confirmed`
  );
}

export function withdrawReviewMessage(
  toAddress: string,
  amount: number,
  balance: number
): string {
  return (
    `*Withdrawal Review*\n\n` +
    `*To*\n\`${toAddress}\`\n\n` +
    `*Amount*\n\`${amount} SOL\`\n\n` +
    `*Current Balance*\n\`${balance.toFixed(4)} SOL\`\n\n` +
    `*Remaining After*\n\`${(balance - amount).toFixed(4)} SOL\`\n\n` +
    `*Network*\nSolana Mainnet\n\n` +
    `Confirm to send.`
  );
}

export function withdrawSuccessMessage(
  toAddress: string,
  amount: number,
  txSignature: string
): string {
  const shortTx = `${txSignature.slice(0, 8)}...${txSignature.slice(-8)}`;
  return (
    `*Withdrawal Sent*\n\n` +
    `*To*\n\`${toAddress}\`\n\n` +
    `*Amount*\n\`${amount} SOL\`\n\n` +
    `*Transaction*\n\`${shortTx}\`\n\n` +
    `*Status:* Confirmed`
  );
}

export function helpMessage(): string {
  return (
    `*TokenLaunchBot Help*\n\n` +
    `*Supported Network:* Solana (SPL Tokens only)\n\n` +
    `*Minimum Wallet Balance:* ${DEPLOYMENT_FEE} SOL\n` +
    `_This covers token creation, creator buy, and all on-chain fees._\n\n` +
    `*How it works:*\n` +
    `1. /create — Enter token details\n` +
    `2. /review — Check everything looks right\n` +
    `3. /launch — Choose launchpad, set creator buy & market cap target\n` +
    `4. /panel — Manage your token after launch\n\n` +
    `*Required fields:* Name, Symbol, Supply, Decimals\n\n` +
    `*Optional:* Description, Logo, Website, Telegram, Twitter, authority settings\n\n` +
    `The bot uses a single dedicated deployment wallet. Use /wallet to check your balance.`
  );
}

export function reviewMessage(
  token: TokenConfig,
  walletAddress: string,
  fee: number
): string {
  const lines: string[] = [];
  lines.push(`*Deployment Review*\n`);
  lines.push(`*Token Details*`);
  lines.push(`Name: \`${token.name}\``);
  lines.push(`Symbol: \`${token.symbol}\``);
  lines.push(`Total Supply: \`${(token.supply ?? 0).toLocaleString()}\``);
  lines.push(`Decimals: \`${token.decimals ?? 9}\``);

  if (token.description) lines.push(`Description: ${token.description}`);
  if (token.logoUrl) lines.push(`Logo: ${token.logoUrl}`);
  if (token.website) lines.push(`Website: ${token.website}`);
  if (token.telegram) lines.push(`Telegram: ${token.telegram}`);
  if (token.twitter) lines.push(`Twitter: ${token.twitter}`);

  lines.push(`\n*Authority Settings*`);
  lines.push(`Revoke Mint: ${token.revokeMint ? "Yes" : "No"}`);
  lines.push(`Revoke Freeze: ${token.revokeFreeze ? "Yes" : "No"}`);

  lines.push(`\n*Deployment*`);
  lines.push(`Wallet: \`${walletAddress}\``);
  lines.push(`Min wallet balance: \`${fee} SOL\``);
  lines.push(`Network: Solana Mainnet`);

  lines.push(`\nReady to launch? Use /launch to continue.`);
  return lines.join("\n");
}

/** Simple 2-option launchpad selector — no descriptions. */
export function launchpadSelectMessage(tokenName: string, tokenSymbol: string): string {
  return (
    `*Select Launchpad*\n\n` +
    `Token: *${tokenName}* (${tokenSymbol})\n\n` +
    `Choose where to launch your coin:`
  );
}

/** Step 2: how much SOL should the creator buy on launch? */
export function creatorBuyMessage(launchpad: string, balance: number): string {
  return (
    `*Creator Buy*\n\n` +
    `Launchpad: *${launchpad === "pumpfun" ? "Pump.fun" : "Raydium"}*\n` +
    `Wallet balance: \`${balance.toFixed(4)} SOL\`\n\n` +
    `How much SOL do you want to invest as the creator?\n` +
    `_This amount will be used to buy your own token on launch._`
  );
}

/** Step 3: what market cap (USD) should trigger the auto-sell? */
export function targetMcapMessage(creatorBuySol: number): string {
  const buyStr = creatorBuySol > 0 ? `\`${creatorBuySol} SOL\`` : "_none_";
  return (
    `*Auto-Sell Target*\n\n` +
    `Creator buy: ${buyStr}\n\n` +
    `At what market cap (USD) should the bot automatically sell all your creator tokens?\n\n` +
    `_The bot monitors the market cap every 30 seconds and sells everything when the target is hit._`
  );
}

/** Step 4: DEX Screener options with live prices. */
export function dexOptionsMessage(
  prices: DexServicePrices,
  balance: number,
  creatorBuySol: number,
  targetMcap: number
): string {
  const mcapStr = targetMcap > 0
    ? `$${targetMcap.toLocaleString()}`
    : "No auto-sell";

  const lines: string[] = [
    `*DEX Screener Options* _(optional)_\n`,
    `Creator buy: \`${creatorBuySol > 0 ? creatorBuySol + " SOL" : "none"}\``,
    `Auto-sell at: \`${mcapStr}\``,
    `Wallet: \`${balance.toFixed(4)} SOL\`\n`,
    `*DEX Update* — ${fmtSolUsd(prices.updateSol, prices.updateUsd)}`,
    `_Adds/updates your token info on DEX Screener._\n`,
    `*DEX Boost* — ${fmtSolUsd(prices.boostSol, prices.boostUsd)}`,
    `_Boosts your token to the trending section._\n`,
    `Toggle the options below, then tap *Confirm & Launch*.\n`,
    `_SOL rate: $${prices.solUsd.toFixed(2)}/SOL_`,
  ];
  return lines.join("\n");
}

export function successMessage(
  mintAddress: string,
  txSignature: string,
  solscanUrl: string,
  timestamp: string
): string {
  const shortTx = `${txSignature.slice(0, 8)}...${txSignature.slice(-8)}`;
  return (
    `*Token Deployed Successfully* 🚀\n\n` +
    `*Mint Address*\n\`${mintAddress}\`\n\n` +
    `*Transaction*\n\`${shortTx}\`\n\n` +
    `*Solscan*\n${solscanUrl}\n\n` +
    `*Status:* Confirmed\n` +
    `*Time:* ${new Date(timestamp).toUTCString()}\n\n` +
    `Tap *Token Panel* to manage your token.`
  );
}

export function pumpfunSuccessMessage(
  mintAddress: string,
  txSignature: string,
  viewUrl: string,
  timestamp: string,
  creatorBuySol: number,
  targetMcapUsd: number
): string {
  const shortTx = `${txSignature.slice(0, 8)}...${txSignature.slice(-8)}`;
  const lines: string[] = [
    `*Token Live on Pump.fun* 🟣\n`,
    `*Mint Address*\n\`${mintAddress}\`\n`,
    `*Transaction*\n\`${shortTx}\`\n`,
    `*Pump.fun Page*\n${viewUrl}\n`,
    `*Status:* Confirmed`,
    `*Time:* ${new Date(timestamp).toUTCString()}`,
  ];
  if (creatorBuySol > 0) {
    lines.push(`\n*Creator Buy:* \`${creatorBuySol} SOL\` purchased on launch.`);
  }
  if (targetMcapUsd > 0) {
    lines.push(
      `*Auto-Sell Target:* \`$${targetMcapUsd.toLocaleString()}\` market cap — the bot will sell automatically when hit.`
    );
  }
  lines.push(`\nTap *Token Panel* to manage your token.`);
  return lines.join("\n");
}

export function raydiumSuccessMessage(
  mintAddress: string,
  txSignature: string,
  solscanUrl: string,
  timestamp: string,
  targetMcapUsd: number
): string {
  const shortTx = `${txSignature.slice(0, 8)}...${txSignature.slice(-8)}`;
  const raydiumUrl = `https://raydium.io/liquidity/create-pool/?token=${mintAddress}`;
  const lines: string[] = [
    `*Token Deployed — Ready for Raydium* 🔵\n`,
    `*Mint Address*\n\`${mintAddress}\`\n`,
    `*Transaction*\n\`${shortTx}\`\n`,
    `*Solscan*\n${solscanUrl}\n`,
    `*Status:* Confirmed`,
    `*Time:* ${new Date(timestamp).toUTCString()}\n`,
    `*Create Raydium Pool:*\n${raydiumUrl}`,
  ];
  if (targetMcapUsd > 0) {
    lines.push(
      `\n*Auto-Sell Target:* \`$${targetMcapUsd.toLocaleString()}\` market cap — the bot monitors DEX Screener and notifies you when hit.`
    );
  }
  lines.push(`\nTap *Token Panel* to manage your token.`);
  return lines.join("\n");
}

export function autoSellExecutedMessage(
  mintAddress: string,
  txSignature: string,
  marketCapUsd: number,
  solReceived?: number
): string {
  const shortTx = `${txSignature.slice(0, 8)}...${txSignature.slice(-8)}`;
  return (
    `*Auto-Sell Triggered* 💰\n\n` +
    `*Mint:* \`${mintAddress}\`\n` +
    `*Market Cap Hit:* \`$${marketCapUsd.toLocaleString()}\`\n` +
    (solReceived !== undefined ? `*SOL Received:* \`${solReceived.toFixed(4)} SOL\`\n` : ``) +
    `*Transaction:* \`${shortTx}\`\n\n` +
    `*Status:* All creator tokens sold.`
  );
}

export function autoSellNotifyMessage(
  mintAddress: string,
  marketCapUsd: number
): string {
  return (
    `*Market Cap Target Reached!* 🎯\n\n` +
    `*Mint:* \`${mintAddress}\`\n` +
    `*Current Market Cap:* \`$${marketCapUsd.toLocaleString()}\`\n\n` +
    `Your target has been reached. Use Token Panel to sell your tokens now.`
  );
}

export function errorMessage(err: string): string {
  return `*Deployment Failed*\n\n${err}\n\nUse /reset to start over or /launch to retry.`;
}

export function insufficientFundsMessage(
  balance: number,
  required: number,
  breakdown?: { label: string; sol: number }[]
): string {
  const needed = (required - balance).toFixed(4);
  const lines = [
    `*Insufficient Funds*\n`,
    `*Current balance:* \`${balance.toFixed(4)} SOL\``,
    `*Required:* \`${required.toFixed(4)} SOL\``,
    `*Still needed:* \`${needed} SOL\``,
  ];
  if (breakdown && breakdown.length > 0) {
    lines.push(`\n*Breakdown:*`);
    for (const item of breakdown) {
      lines.push(`• ${item.label}: \`${item.sol.toFixed(4)} SOL\``);
    }
  }
  lines.push(`\nDeposit SOL to your wallet and use /wallet to verify your balance.`);
  return lines.join("\n");
}
