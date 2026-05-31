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
  getAssociatedTokenAddress,
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

export interface GeneratedWallet {
  address: string;
  privateKey: string;
}

export function generateNewWallet(): GeneratedWallet {
  const keypair = Keypair.generate();
  const address = keypair.publicKey.toBase58();
  const privateKey = bs58.encode(keypair.secretKey);
  return { address, privateKey };
}

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

  const signature = await sendAndConfirmTransaction(connection, tx, [payer], {
    commitment: "confirmed",
  });

  return signature;
}

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
