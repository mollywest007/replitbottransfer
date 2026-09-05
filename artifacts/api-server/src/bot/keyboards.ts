import { Markup } from "telegraf";
import type { DexServicePrices } from "./dex-pricing";
import { fmtSolUsd } from "./dex-pricing";

/** Launchpad selection — Pump.fun and Raydium only. */
export function launchpadKeyboard() {
  return Markup.inlineKeyboard([
    [Markup.button.callback("🟣 Pump.fun", "launch_pumpfun")],
    [Markup.button.callback("🔵 Raydium", "launch_raydium")],
    [Markup.button.callback("❌ Cancel", "launch_cancel")],
  ]);
}

/** Creator buy amount presets (SOL). */
export function creatorBuyKeyboard() {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback("0.5 SOL", "cb_buy:0.5"),
      Markup.button.callback("1 SOL", "cb_buy:1"),
    ],
    [
      Markup.button.callback("2 SOL", "cb_buy:2"),
      Markup.button.callback("5 SOL", "cb_buy:5"),
    ],
    [Markup.button.callback("✏️ Custom amount", "cb_buy:custom")],
    [Markup.button.callback("Skip (no buy)", "cb_buy:skip")],
    [Markup.button.callback("❌ Cancel", "launch_cancel")],
  ]);
}

/** Target market cap presets (USD). */
export function targetMcapKeyboard() {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback("$10K", "cb_mcap:10000"),
      Markup.button.callback("$50K", "cb_mcap:50000"),
    ],
    [
      Markup.button.callback("$100K", "cb_mcap:100000"),
      Markup.button.callback("$500K", "cb_mcap:500000"),
    ],
    [Markup.button.callback("✏️ Custom target", "cb_mcap:custom")],
    [Markup.button.callback("No auto-sell", "cb_mcap:skip")],
    [Markup.button.callback("❌ Cancel", "launch_cancel")],
  ]);
}

/** DEX Screener options with live prices and toggle state. */
export function dexOptionsKeyboard(
  prices: DexServicePrices,
  dexUpdate: boolean,
  dexBoost: boolean
) {
  const updateLabel = `${dexUpdate ? "✅" : "☐"} DEX Update — ${fmtSolUsd(prices.updateSol, prices.updateUsd)}`;
  const boostLabel  = `${dexBoost  ? "✅" : "☐"} DEX Boost  — ${fmtSolUsd(prices.boostSol,  prices.boostUsd)}`;
  return Markup.inlineKeyboard([
    [Markup.button.callback(updateLabel, "dex_toggle_update")],
    [Markup.button.callback(boostLabel,  "dex_toggle_boost")],
    [Markup.button.callback("🚀 Confirm & Launch", "dex_confirm")],
    [Markup.button.callback("❌ Cancel", "launch_cancel")],
  ]);
}

export function walletRefreshKeyboard() {
  return Markup.inlineKeyboard([
    [Markup.button.callback("🔄 Refresh Balance", "wallet_refresh")],
  ]);
}

export function mainMenuKeyboard() {
  return Markup.keyboard([
    ["Create Token", "Wallet Info"],
    ["Withdraw SOL", "Review Deployment"],
    ["Launch Token", "Token Panel"],
    ["Help", "Reset"],
  ])
    .resize()
    .persistent()
    .oneTime(false);
}

export function yesNoKeyboard() {
  return Markup.keyboard([["Yes, Launch", "Cancel"]])
    .resize()
    .oneTime(true);
}

export function backKeyboard() {
  return Markup.keyboard([["◀ Back"]])
    .resize()
    .oneTime(false);
}

export function optionalSkipKeyboard() {
  return Markup.keyboard([
    ["Skip", "◀ Back"],
    ["Done with optional fields"],
  ])
    .resize()
    .oneTime(false);
}

export function tokenPanelKeyboard(mintAddress: string) {
  return Markup.inlineKeyboard([
    [Markup.button.callback("💰 Check Balance", `panel_balance:${mintAddress}`)],
    [
      Markup.button.callback("🔥 Burn Half", `panel_burn_half:${mintAddress}`),
      Markup.button.callback("🔥 Burn All", `panel_burn_all:${mintAddress}`),
    ],
    [Markup.button.callback("📤 Transfer Tokens", `panel_transfer:${mintAddress}`)],
    [
      Markup.button.callback("🔒 Revoke Mint", `panel_revoke_mint:${mintAddress}`),
      Markup.button.callback("🔒 Revoke Freeze", `panel_revoke_freeze:${mintAddress}`),
    ],
  ]);
}

export function burnConfirmKeyboard(mintAddress: string, portion: "half" | "all") {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback("Confirm Burn", `panel_burn_confirm:${portion}:${mintAddress}`),
      Markup.button.callback("Cancel", `panel_cancel:${mintAddress}`),
    ],
  ]);
}

export function revokeConfirmKeyboard(
  mintAddress: string,
  type: "mint" | "freeze"
) {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback(
        "Confirm Revoke",
        `panel_revoke_confirm:${type}:${mintAddress}`
      ),
      Markup.button.callback("Cancel", `panel_cancel:${mintAddress}`),
    ],
  ]);
}

export function panelTransferConfirmKeyboard() {
  return Markup.keyboard([["Confirm Transfer", "Cancel"]])
    .resize()
    .oneTime(true);
}

export function authorityInlineKeyboard(
  revokeMint: boolean,
  revokeFreeze: boolean
) {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback(
        `Revoke Mint: ${revokeMint ? "ON" : "OFF"}`,
        "toggle_mint"
      ),
    ],
    [
      Markup.button.callback(
        `Revoke Freeze: ${revokeFreeze ? "ON" : "OFF"}`,
        "toggle_freeze"
      ),
    ],
    [Markup.button.callback("Done", "authority_done")],
  ]);
}
