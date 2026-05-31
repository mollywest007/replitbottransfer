import { Markup } from "telegraf";

export function mainMenuKeyboard() {
  return Markup.keyboard([
    ["Create Token", "Wallet Info"],
    ["Withdraw SOL", "Generate Wallet"],
    ["Review Deployment", "Launch Token"],
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
