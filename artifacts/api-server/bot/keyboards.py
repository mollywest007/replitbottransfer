from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["Create Token", "Wallet Info"],
            ["Withdraw SOL", "Review Deployment"],
            ["Launch Token", "Token Panel"],
            ["Help", "Reset"],
        ],
        resize_keyboard=True,
        is_persistent=True,
        one_time_keyboard=False,
    )


def optional_skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["Skip"], ["Done with optional fields"], ["◀ Back"]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def back_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["◀ Back", "Cancel"]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def authority_inline_keyboard(revoke_mint: bool, revoke_freeze: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{'✅' if revoke_mint else '☐'} Revoke Mint Authority",
            callback_data="toggle_mint",
        )],
        [InlineKeyboardButton(
            f"{'✅' if revoke_freeze else '☐'} Revoke Freeze Authority",
            callback_data="toggle_freeze",
        )],
        [InlineKeyboardButton("Done ✓ Proceed to Launch", callback_data="authority_done")],
        [InlineKeyboardButton("◀ Back", callback_data="back_to_optionals")],
    ])


def launchpad_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟣 Pump.fun", callback_data="launch_pumpfun")],
        [InlineKeyboardButton("🔵 Raydium", callback_data="launch_raydium")],
        [InlineKeyboardButton("◀ Back", callback_data="back_to_authority")],
        [InlineKeyboardButton("❌ Cancel", callback_data="launch_cancel")],
    ])


def creator_buy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("0.5 SOL", callback_data="cb_buy:0.5"),
            InlineKeyboardButton("1 SOL", callback_data="cb_buy:1"),
        ],
        [
            InlineKeyboardButton("2 SOL", callback_data="cb_buy:2"),
            InlineKeyboardButton("5 SOL", callback_data="cb_buy:5"),
        ],
        [InlineKeyboardButton("✏️ Custom amount", callback_data="cb_buy:custom")],
        [InlineKeyboardButton("⏭ Skip (no buy)", callback_data="cb_buy:skip")],
        [InlineKeyboardButton("◀ Back", callback_data="back_to_launchpad")],
        [InlineKeyboardButton("❌ Cancel", callback_data="launch_cancel")],
    ])


def target_mcap_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("$10K", callback_data="cb_mcap:10000"),
            InlineKeyboardButton("$50K", callback_data="cb_mcap:50000"),
        ],
        [
            InlineKeyboardButton("$100K", callback_data="cb_mcap:100000"),
            InlineKeyboardButton("$500K", callback_data="cb_mcap:500000"),
        ],
        [InlineKeyboardButton("✏️ Custom target", callback_data="cb_mcap:custom")],
        [InlineKeyboardButton("⏭ No auto-sell", callback_data="cb_mcap:skip")],
        [InlineKeyboardButton("◀ Back", callback_data="back_to_creator_buy")],
        [InlineKeyboardButton("❌ Cancel", callback_data="launch_cancel")],
    ])


def dex_options_keyboard(prices: dict, dex_update: bool, dex_boost: bool) -> InlineKeyboardMarkup:
    upd = f"{'✅' if dex_update else '☐'} DEX Update — {prices['update_sol']:.4f} SOL (${prices['update_usd']})"
    bst = f"{'✅' if dex_boost  else '☐'} DEX Boost  — {prices['boost_sol']:.4f} SOL (${prices['boost_usd']})"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(upd, callback_data="dex_toggle_update")],
        [InlineKeyboardButton(bst, callback_data="dex_toggle_boost")],
        [InlineKeyboardButton("🚀 Confirm & Launch", callback_data="dex_confirm")],
        [InlineKeyboardButton("◀ Back", callback_data="back_to_target_mcap")],
        [InlineKeyboardButton("❌ Cancel", callback_data="launch_cancel")],
    ])


def token_panel_keyboard(mint_address: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Refresh Balance", callback_data=f"panel_balance:{mint_address}")],
        [
            InlineKeyboardButton("🔥 Burn Half", callback_data=f"panel_burn_half:{mint_address}"),
            InlineKeyboardButton("🔥 Burn All", callback_data=f"panel_burn_all:{mint_address}"),
        ],
        [InlineKeyboardButton("📤 Transfer Tokens", callback_data=f"panel_transfer:{mint_address}")],
        [
            InlineKeyboardButton("🔒 Revoke Mint", callback_data=f"panel_revoke_mint:{mint_address}"),
            InlineKeyboardButton("🔒 Revoke Freeze", callback_data=f"panel_revoke_freeze:{mint_address}"),
        ],
        [InlineKeyboardButton("Home", callback_data="back_to_home")],
    ])


def burn_confirm_keyboard(mint_address: str, portion: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 Confirm Burn", callback_data=f"panel_burn_confirm:{portion}:{mint_address}"),
            InlineKeyboardButton("Cancel", callback_data=f"panel_cancel:{mint_address}"),
        ],
    ])


def revoke_confirm_keyboard(mint_address: str, authority_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔒 Confirm Revoke", callback_data=f"panel_revoke_confirm:{authority_type}:{mint_address}"),
            InlineKeyboardButton("Cancel", callback_data=f"panel_cancel:{mint_address}"),
        ],
    ])


def wallet_refresh_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh Balance", callback_data="wallet_refresh")],
        [InlineKeyboardButton("✅ Verify Deposit", callback_data="verify_deposit")],
        [InlineKeyboardButton("Home", callback_data="back_to_home")],
    ])


def generate_wallet_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Generate Wallet", callback_data="generate_wallet")],
        [InlineKeyboardButton("Home", callback_data="back_to_home")],
    ])
