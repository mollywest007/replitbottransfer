/**
 * DEX Screener service pricing + SOL/USD rate.
 * Fetches the live SOL price from CoinGecko (free tier, no key needed) and
 * converts known DEX Screener USD prices into their SOL equivalent.
 * Cached for 30 minutes; stale cache is kept on fetch failure.
 */
import { logger } from "../lib/logger";

// Known DEX Screener service costs in USD.
// Update these constants if DEX Screener changes their pricing.
export const DEX_UPDATE_USD = 299;  // Token Info / profile update
export const DEX_BOOST_USD  = 30;   // Single boost unit

export interface DexServicePrices {
  solUsd: number;
  updateUsd: number;
  boostUsd: number;
  updateSol: number;
  boostSol: number;
  lastFetched: Date | null;
}

const CACHE_TTL_MS = 30 * 60 * 1000; // 30 min

let _cache: DexServicePrices = {
  solUsd: 150,
  updateUsd: DEX_UPDATE_USD,
  boostUsd: DEX_BOOST_USD,
  updateSol: DEX_UPDATE_USD / 150,
  boostSol: DEX_BOOST_USD / 150,
  lastFetched: null,
};

/** Returns current DEX service prices, refreshing from CoinGecko if stale. */
export async function fetchDexPrices(): Promise<DexServicePrices> {
  const now = Date.now();
  if (_cache.lastFetched && now - _cache.lastFetched.getTime() < CACHE_TTL_MS) {
    return _cache;
  }

  try {
    const res = await fetch(
      "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd",
      { signal: AbortSignal.timeout(8_000) }
    );
    if (!res.ok) throw new Error(`CoinGecko HTTP ${res.status}`);
    const data = (await res.json()) as { solana?: { usd?: number } };
    const solUsd = data?.solana?.usd;
    if (!solUsd || solUsd <= 0) throw new Error("CoinGecko: invalid SOL price");

    _cache = {
      solUsd,
      updateUsd: DEX_UPDATE_USD,
      boostUsd: DEX_BOOST_USD,
      updateSol: DEX_UPDATE_USD / solUsd,
      boostSol: DEX_BOOST_USD / solUsd,
      lastFetched: new Date(),
    };
    logger.info({ solUsd }, "DEX pricing refreshed");
  } catch (err) {
    logger.warn({ err }, "Failed to refresh SOL price — using cached value");
  }

  return _cache;
}

/** Formats a SOL value with 4 decimal places and a USD equivalent. */
export function fmtSolUsd(sol: number, usd: number): string {
  return `${sol.toFixed(4)} SOL ($${usd})`;
}
