import { Markup } from "telegraf";

export function mainMenuKeyboard() {
  return Markup.keyboard([
    ["Create Token", "Wallet Info"],
    ["Withdraw SOL", "Review Deployment"],
    ["Launch Token", "Help"],
    ["Reset"],
  ])
    .resize()
    .oneTime(false);
}

export function yesNoKeyboard() {
  return Markup.keyboard([["Yes, Launch", "Cancel"]])
    .resize()
    .oneTime(true);
}

export function withdrawConfirmKeyboard() {
  return Markup.keyboard([["Confirm Withdrawal", "Cancel"]])
    .resize()
    .oneTime(true);
}

export function optionalSkipKeyboard() {
  return Markup.keyboard([["Skip", "Done with optional fields"]])
    .resize()
    .oneTime(false);
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
