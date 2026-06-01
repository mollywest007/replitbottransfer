/**
 * Pump.fun launchpad integration.
 * Anchor and pumpdotfun-sdk are loaded lazily (dynamic import) so their
 * fetch polyfills don't pollute the global scope at startup.
 * Raydium uses the standard SPL deployToken flow — pool creation is done by the user on Raydium UI.
 */
import {
  Keypair,
  PublicKey,
  Transaction,
  VersionedTransaction,
} from "@solana/web3.js";
import { logger } from "../lib/logger";
import type { TokenConfig } from "./session";
import { connection, getDeploymentKeypair, getTokenBalance } from "./solana";

export interface LaunchpadDeployResult {
  mintAddress: string;
  txSignature: string;
  viewUrl: string;
  timestamp: string;
}

export interface SellResult {
  txSignature: string;
  mintAddress: string;
}

/** Minimum SOL needed for Pump.fun token creation (~0.02 SOL fee, 0.05 for safety). */
export const PUMPFUN_MIN_SOL = 0.05;

async function fetchLogoBlob(logoUrl?: string): Promise<Blob> {
  if (logoUrl) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 8000);
      const res = await fetch(logoUrl, { signal: controller.signal });
      clearTimeout(timer);
      if (res.ok) {
        const buf = await res.arrayBuffer();
        const contentType = res.headers.get("content-type") ?? "image/png";
        return new Blob([buf], { type: contentType });
      }
    } catch {
      // fall through to placeholder
    }
  }
  // 1×1 transparent PNG placeholder
  const png = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "base64"
  );
  return new Blob([png], { type: "image/png" });
}

/**
 * Loads Anchor + PumpFunSDK lazily to prevent their fetch polyfills
 * from corrupting the global AbortSignal at startup.
 */
async function loadPumpFunSdk(payer: Keypair) {
  const [{ AnchorProvider }, { PumpFunSDK }] = await Promise.all([
    import("@coral-xyz/anchor") as Promise<{
      AnchorProvider: typeof import("@coral-xyz/anchor").AnchorProvider;
    }>,
    import("pumpdotfun-sdk") as Promise<{
      PumpFunSDK: typeof import("pumpdotfun-sdk").PumpFunSDK;
    }>,
  ]);

  const anchorWallet = {
    payer,
    publicKey: payer.publicKey,
    async signTransaction<T extends Transaction | VersionedTransaction>(tx: T): Promise<T> {
      if (tx instanceof VersionedTransaction) {
        tx.sign([payer]);
      } else {
        (tx as Transaction).partialSign(payer);
      }
      return tx;
    },
    async signAllTransactions<T extends Transaction | VersionedTransaction>(
      txs: T[]
    ): Promise<T[]> {
      return txs.map((tx) => {
        if (tx instanceof VersionedTransaction) {
          tx.sign([payer]);
        } else {
          (tx as Transaction).partialSign(payer);
        }
        return tx;
      });
    },
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const provider = new AnchorProvider(connection, anchorWallet as any, {
    commitment: "confirmed",
  });

  return new PumpFunSDK(provider);
}

export async function deployPumpFun(
  config: TokenConfig,
  creatorBuyAmountSol = 0
): Promise<LaunchpadDeployResult> {
  const payer = getDeploymentKeypair();
  const mintKeypair = Keypair.generate();
  const sdk = await loadPumpFunSdk(payer);

  const logoBlob = await fetchLogoBlob(config.logoUrl);

  const metadata = {
    name: config.name!,
    symbol: config.symbol!,
    description: config.description ?? `${config.name} token launched via TokenLaunchBot`,
    file: logoBlob,
    twitter: config.twitter,
    telegram: config.telegram,
    website: config.website,
  };

  // Convert SOL to lamports (bigint)
  const buyLamports = BigInt(Math.round(creatorBuyAmountSol * 1e9));

  logger.info(
    { mint: mintKeypair.publicKey.toBase58(), creatorBuyAmountSol },
    "Deploying token on Pump.fun"
  );

  const result = await sdk.createAndBuy(
    payer,
    mintKeypair,
    metadata,
    buyLamports,
    BigInt(100),
    { unitLimit: 250_000, unitPrice: 250_000 },
    "confirmed",
    "finalized"
  );

  if (!result.success || !result.signature) {
    throw new Error(
      `Pump.fun deployment failed: ${result.error ? String(result.error) : "unknown error"}`
    );
  }

  const mintAddress = mintKeypair.publicKey.toBase58();
  return {
    mintAddress,
    txSignature: result.signature,
    viewUrl: `https://pump.fun/coin/${mintAddress}`,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Sells all creator tokens on Pump.fun.
 * Called automatically by the market cap monitor when the target is hit.
 */
export async function sellAllPumpFun(mintAddress: string): Promise<SellResult> {
  const payer = getDeploymentKeypair();
  const sdk = await loadPumpFunSdk(payer);

  const wallet = payer.publicKey.toBase58();
  const bal = await getTokenBalance(mintAddress, wallet);
  if (bal.rawAmount === BigInt(0)) {
    throw new Error("No tokens to sell — creator balance is 0");
  }

  logger.info(
    { mint: mintAddress, rawAmount: bal.rawAmount.toString() },
    "Auto-selling all Pump.fun tokens"
  );

  const result = await sdk.sell(
    payer,
    new PublicKey(mintAddress),
    bal.rawAmount,
    BigInt(100),   // 1% slippage basis points
    { unitLimit: 250_000, unitPrice: 250_000 },
    "confirmed",
    "finalized"
  );

  if (!result.success || !result.signature) {
    throw new Error(
      `Pump.fun sell failed: ${result.error ? String(result.error) : "unknown error"}`
    );
  }

  return { txSignature: result.signature, mintAddress };
}
