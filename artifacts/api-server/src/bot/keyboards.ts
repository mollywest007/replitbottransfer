import { Markup } from "telegraf";

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
    .oneTime(false);
}

export function yesNoKeyboard() {
  return Markup.keyboard([["Yes, Launch", "Cancel"]])
    .resize()
    .oneTime(true);
}

/** Shown during required field collection (all steps except the very first). */
export function backKeyboard() {
  return Markup.keyboard([["◀ Back"]])
    .resize()
    .oneTime(false);
}

/** Shown during optional field collection: skip, back, or finish. */
export function optionalSkipKeyboard() {
  return Markup.keyboard([
    ["Skip", "◀ Back"],
    ["Done with optional fields"],
  ])
    .resize()
    .oneTime(false);
}

/** Shown while entering a withdrawal address or amount. */
export function withdrawInputKeyboard() {
  return Markup.keyboard([["◀ Back", "Cancel"]])
    .resize()
    .oneTime(false);
}

/** Shown on the withdrawal review/confirm screen. */
export function withdrawConfirmKeyboard() {
  return Markup.keyboard([["Confirm Withdrawal"], ["◀ Back", "Cancel"]])
    .resize()
    .oneTime(true);
}

/** Token control panel inline keyboard. */
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

/** Burn confirmation inline keyboard. */
export function burnConfirmKeyboard(mintAddress: string, portion: "half" | "all") {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback("Confirm Burn", `panel_burn_confirm:${portion}:${mintAddress}`),
      Markup.button.callback("Cancel", `panel_cancel:${mintAddress}`),
    ],
  ]);
}

/** Revoke confirmation inline keyboard. */
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

/** Keyboard shown during panel transfer flow. */
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
