import {
  Connection,
  Keypair,
  PublicKey,
  SystemProgram,
  Transaction,
  sendAndConfirmTransaction,
  LAMPORTS_PER_SOL,
} from "@solana/web3.js";
import {
  createInitializeMintInstruction,
  createAssociatedTokenAccountInstruction,
  createMintToInstruction,
  createBurnInstruction,
  createTransferInstruction,
  createSetAuthorityInstruction,
  getAssociatedTokenAddress,
  getOrCreateAssociatedTokenAccount,
  getAccount,
  getMint,
  AuthorityType,
  MINT_SIZE,
  TOKEN_PROGRAM_ID,
  getMinimumBalanceForRentExemptMint,
} from "@solana/spl-token";
import bs58 from "bs58";
import { logger } from "../lib/logger";
import type { TokenConfig } from "./session";

const RPC_ENDPOINT = "https://api.mainnet-beta.solana.com";

export const connection = new Connection(RPC_ENDPOINT, "confirmed");

export function getDeploymentKeypair(): Keypair {
  const pk = process.env["PRIVATE_KEY"];
  if (!pk) throw new Error("PRIVATE_KEY not configured");
  const decoded = bs58.decode(pk);
  return Keypair.fromSecretKey(decoded);
}

export function getDeploymentWallet(): string {
  return process.env["WALLET_ADDRESS"] ?? "";
}

export async function getWalletBalance(address: string): Promise<number> {
  const pub = new PublicKey(address);
  const lamports = await connection.getBalance(pub);
  return lamports / LAMPORTS_PER_SOL;
}

// ── Token balance ─────────────────────────────────────────────────────────────

export interface TokenBalance {
  rawAmount: bigint;
  decimals: number;
  uiAmount: number;
}

export async function getTokenBalance(
  mintAddress: string,
  walletAddress: string
): Promise<TokenBalance> {
  const mint = new PublicKey(mintAddress);
  const wallet = new PublicKey(walletAddress);
  const ata = await getAssociatedTokenAddress(mint, wallet);

  try {
    const [account, mintInfo] = await Promise.all([
      getAccount(connection, ata),
      getMint(connection, mint),
    ]);
    const rawAmount = account.amount;
    const decimals = mintInfo.decimals;
    const uiAmount = Number(rawAmount) / Math.pow(10, decimals);
    return { rawAmount, decimals, uiAmount };
  } catch {
    // ATA may not exist yet or token balance is zero
    const mintInfo = await getMint(connection, mint).catch(() => ({ decimals: 9 }));
    return { rawAmount: BigInt(0), decimals: mintInfo.decimals, uiAmount: 0 };
  }
}

// ── Burn ──────────────────────────────────────────────────────────────────────

export async function burnTokens(
  mintAddress: string,
  rawAmount: bigint
): Promise<string> {
  const payer = getDeploymentKeypair();
  const mint = new PublicKey(mintAddress);
  const ata = await getAssociatedTokenAddress(mint, payer.publicKey);

  const tx = new Transaction().add(
    createBurnInstruction(ata, mint, payer.publicKey, rawAmount)
  );

  logger.info({ mintAddress, rawAmount: rawAmount.toString() }, "Burning tokens");

  return sendAndConfirmTransaction(connection, tx, [payer], {
    commitment: "confirmed",
  });
}

// ── Transfer ──────────────────────────────────────────────────────────────────

export async function transferSplTokens(
  mintAddress: string,
  toAddress: string,
  rawAmount: bigint
): Promise<string> {
  const payer = getDeploymentKeypair();
  const mint = new PublicKey(mintAddress);
  const toPubkey = new PublicKey(toAddress);

  const fromAta = await getAssociatedTokenAddress(mint, payer.publicKey);
  const toAta = await getOrCreateAssociatedTokenAccount(
    connection,
    payer,
    mint,
    toPubkey
  );

  const tx = new Transaction().add(
    createTransferInstruction(
      fromAta,
      toAta.address,
      payer.publicKey,
      rawAmount
    )
  );

  logger.info(
    { mintAddress, toAddress, rawAmount: rawAmount.toString() },
    "Transferring tokens"
  );

  return sendAndConfirmTransaction(connection, tx, [payer], {
    commitment: "confirmed",
  });
}

// ── Revoke authorities ────────────────────────────────────────────────────────

export async function revokeMintAuthority(mintAddress: string): Promise<string> {
  const payer = getDeploymentKeypair();
  const mint = new PublicKey(mintAddress);

  const tx = new Transaction().add(
    createSetAuthorityInstruction(
      mint,
      payer.publicKey,
      AuthorityType.MintTokens,
      null
    )
  );

  logger.info({ mintAddress }, "Revoking mint authority");

  return sendAndConfirmTransaction(connection, tx, [payer], {
    commitment: "confirmed",
  });
}

export async function revokeFreezeAuthority(
  mintAddress: string
): Promise<string> {
  const payer = getDeploymentKeypair();
  const mint = new PublicKey(mintAddress);

  const tx = new Transaction().add(
    createSetAuthorityInstruction(
      mint,
      payer.publicKey,
      AuthorityType.FreezeAccount,
      null
    )
  );

  logger.info({ mintAddress }, "Revoking freeze authority");

  return sendAndConfirmTransaction(connection, tx, [payer], {
    commitment: "confirmed",
  });
}

// ── Withdraw SOL ──────────────────────────────────────────────────────────────

export async function withdrawSol(
  toAddress: string,
  amountSol: number
): Promise<string> {
  const payer = getDeploymentKeypair();
  const toPubkey = new PublicKey(toAddress);
  const lamports = Math.round(amountSol * LAMPORTS_PER_SOL);

  const tx = new Transaction().add(
    SystemProgram.transfer({
      fromPubkey: payer.publicKey,
      toPubkey,
      lamports,
    })
  );

  logger.info({ toAddress, amountSol }, "Withdrawing SOL");

  return sendAndConfirmTransaction(connection, tx, [payer], {
    commitment: "confirmed",
  });
}

// ── Deploy token ──────────────────────────────────────────────────────────────

export interface DeployResult {
  mintAddress: string;
  txSignature: string;
  solscanUrl: string;
  timestamp: string;
}

export async function deployToken(
  config: TokenConfig,
  feeSol: number
): Promise<DeployResult> {
  const payer = getDeploymentKeypair();
  const mintKeypair = Keypair.generate();

  const lamportsForMint = await getMinimumBalanceForRentExemptMint(connection);
  const supply = config.supply ?? 1_000_000_000;
  const decimals = config.decimals ?? 9;
  const supplyWithDecimals = BigInt(supply) * BigInt(10 ** decimals);

  const ata = await getAssociatedTokenAddress(
    mintKeypair.publicKey,
    payer.publicKey
  );

  const tx = new Transaction();

  tx.add(
    SystemProgram.createAccount({
      fromPubkey: payer.publicKey,
      newAccountPubkey: mintKeypair.publicKey,
      space: MINT_SIZE,
      lamports: lamportsForMint,
      programId: TOKEN_PROGRAM_ID,
    })
  );

  tx.add(
    createInitializeMintInstruction(
      mintKeypair.publicKey,
      decimals,
      payer.publicKey,
      config.revokeFreeze ? null : payer.publicKey
    )
  );

  tx.add(
    createAssociatedTokenAccountInstruction(
      payer.publicKey,
      ata,
      payer.publicKey,
      mintKeypair.publicKey
    )
  );

  tx.add(
    createMintToInstruction(
      mintKeypair.publicKey,
      ata,
      payer.publicKey,
      supplyWithDecimals
    )
  );

  logger.info(
    { mint: mintKeypair.publicKey.toBase58(), feeSol },
    "Deploying SPL token"
  );

  const signature = await sendAndConfirmTransaction(
    connection,
    tx,
    [payer, mintKeypair],
    { commitment: "confirmed" }
  );

  const mintAddress = mintKeypair.publicKey.toBase58();

  return {
    mintAddress,
    txSignature: signature,
    solscanUrl: `https://solscan.io/token/${mintAddress}`,
    timestamp: new Date().toISOString(),
  };
}
