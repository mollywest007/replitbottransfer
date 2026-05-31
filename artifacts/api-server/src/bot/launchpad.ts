/**
 * Pump.fun launchpad integration.
 * Anchor and pumpdotfun-sdk are loaded lazily (dynamic import) so their
 * fetch polyfills don't pollute the global scope at startup.
 * Raydium uses the standard SPL deployToken flow — pool creation is done by the user on Raydium UI.
 */
import {
  Keypair,
  Transaction,
  VersionedTransaction,
} from "@solana/web3.js";
import { logger } from "../lib/logger";
import type { TokenConfig } from "./session";
import { connection, getDeploymentKeypair } from "./solana";

export interface LaunchpadDeployResult {
  mintAddress: string;
  txSignature: string;
  viewUrl: string;
  timestamp: string;
}

/** Minimum SOL needed for Pump.fun token creation (their fee ~0.02 SOL, 0.05 for safety). */
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

export async function deployPumpFun(config: TokenConfig): Promise<LaunchpadDeployResult> {
  // Lazy-load anchor and pumpdotfun-sdk to prevent their fetch polyfills
  // from running at startup and breaking Telegraf's native AbortSignal usage.
  const [{ AnchorProvider }, { PumpFunSDK }] = await Promise.all([
    import("@coral-xyz/anchor") as Promise<{ AnchorProvider: typeof import("@coral-xyz/anchor").AnchorProvider }>,
    import("pumpdotfun-sdk") as Promise<{ PumpFunSDK: typeof import("pumpdotfun-sdk").PumpFunSDK }>,
  ]);

  const payer = getDeploymentKeypair();
  const mintKeypair = Keypair.generate();

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
    async signAllTransactions<T extends Transaction | VersionedTransaction>(txs: T[]): Promise<T[]> {
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

  const sdk = new PumpFunSDK(provider);
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

  logger.info(
    { mint: mintKeypair.publicKey.toBase58() },
    "Deploying token on Pump.fun"
  );

  const result = await sdk.createAndBuy(
    payer,
    mintKeypair,
    metadata,
    BigInt(0),
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
