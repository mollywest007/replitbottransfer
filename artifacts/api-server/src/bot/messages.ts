import type { TokenConfig } from "./session";

export const DEPLOYMENT_FEE = 5; // SOL — minimum fee

export function mainMenuMessage(): string {
  return (
    `*TokenLaunchBot* — Solana SPL Token Deployer\n\n` +
    `Deploy tokens on Solana in minutes.\n\n` +
    `*Commands*\n` +
    `/create — Start token creation\n` +
    `/wallet — Deployment wallet info\n` +
    `/withdraw — Withdraw SOL\n` +
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
    `*Private Key*\n${keyConfigured ? "`Configured ✓`" : "`Not configured ✗`"}\n\n` +
    `*Network*\nSolana Mainnet\n\n` +
    `_This is a fixed deployment wallet. It cannot be changed._`
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
    `*Deployment Fee:* 5–10 SOL\n\n` +
    `*How it works:*\n` +
    `1. /create — Enter token details\n` +
    `2. /review — Check everything looks right\n` +
    `3. /launch — Deploy on-chain\n\n` +
    `*Required fields:* Name, Symbol, Supply, Decimals\n\n` +
    `*Optional:* Description, Logo, Website, Telegram, Twitter, authority settings\n\n` +
    `The bot uses a single dedicated deployment wallet. You cannot change this wallet.`
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
  lines.push(`Fee: \`${fee} SOL\``);
  lines.push(`Network: Solana Mainnet`);

  lines.push(`\nReady to launch? Use /launch to deploy.`);
  return lines.join("\n");
}

export function successMessage(
  mintAddress: string,
  txSignature: string,
  solscanUrl: string,
  timestamp: string
): string {
  const shortTx = `${txSignature.slice(0, 8)}...${txSignature.slice(-8)}`;
  const shortMint = `${mintAddress.slice(0, 8)}...${mintAddress.slice(-8)}`;
  return (
    `*Token Deployed Successfully*\n\n` +
    `*Mint Address*\n\`${mintAddress}\`\n\n` +
    `*Transaction*\n\`${shortMint}\` — \`${shortTx}\`\n\n` +
    `*Solscan*\n${solscanUrl}\n\n` +
    `*Status:* Confirmed\n` +
    `*Time:* ${new Date(timestamp).toUTCString()}`
  );
}

export function errorMessage(err: string): string {
  return `*Deployment Failed*\n\n${err}\n\nUse /reset to start over or /launch to retry.`;
}

export function insufficientFundsMessage(balance: number, fee: number): string {
  return (
    `*Insufficient Funds*\n\n` +
    `Your deployment wallet has \`${balance.toFixed(4)} SOL\`.\n` +
    `Required: \`${fee} SOL\` (fee) + network costs.\n\n` +
    `Please fund the wallet and try again.`
  );
}
