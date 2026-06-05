from config import DEPLOYMENT_FEE, PLATFORM_FEE_USD, DEX_UPDATE_USD, DEX_BOOST_USD


def h(text: str) -> str:
    """Escape special HTML characters in dynamic content."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main_menu_message() -> str:
    return (
        "<b>TokenLaunchBot</b> — Solana SPL Token Deployer\n\n"
        "Deploy tokens on Solana in minutes.\n\n"
        "<b>Commands</b>\n"
        "/create — Start token creation\n"
        "/wallet — Deployment wallet info\n"
        "/withdraw — Withdraw SOL\n"
        "/panel — Token control panel\n"
        "/review — Review deployment details\n"
        "/launch — Deploy your token\n"
        "/reset — Start over\n"
        "/help — Show help"
    )


def wallet_message(address: str, balance: float, key_configured: bool) -> str:
    status = "✅ Configured" if key_configured else "❌ Not configured"
    enough = "✅ Sufficient" if balance >= DEPLOYMENT_FEE else f"⚠️ Need {DEPLOYMENT_FEE - balance:.4f} more SOL"
    return (
        f"<b>💼 Deployment Wallet</b>\n\n"
        f"<b>Address</b>\n<code>{h(address)}</code>\n\n"
        f"<b>Balance</b>\n<code>{balance:.4f} SOL</code> — {enough}\n\n"
        f"<b>Minimum Required</b>\n<code>{DEPLOYMENT_FEE} SOL</code>\n\n"
        f"<b>Private Key</b>\n<code>{status}</code>\n\n"
        f"<b>Network</b>\nSolana Mainnet\n\n"
        f"<i>This is a fixed deployment wallet.</i>"
    )


def help_message() -> str:
    return (
        f"<b>TokenLaunchBot Help</b>\n\n"
        f"<b>Supported Network:</b> Solana (SPL Tokens)\n\n"
        f"<b>Minimum Wallet Balance:</b> <code>{DEPLOYMENT_FEE} SOL</code>\n"
        f"<i>Covers token creation, creator buy, and all on-chain fees.</i>\n\n"
        f"<b>How it works:</b>\n"
        f"1. /create — Enter token details\n"
        f"2. /review — Check everything looks right\n"
        f"3. /launch — Choose launchpad, set creator buy &amp; market cap target\n"
        f"4. /panel — Manage your token after launch\n\n"
        f"<b>Required fields:</b> Name, Symbol\n"
        f"<b>Optional:</b> Description, Logo, Website, Telegram, Twitter\n\n"
        f"The bot uses a single dedicated deployment wallet.\n"
        f"Use /wallet to check your balance.\n\n"
        f"<b>Support</b>\n"
        f"Contact <a href=\"https://t.me/devBernard\">@devBernard</a> on Telegram."
    )


def review_message(token: dict, wallet_address: str) -> str:
    lines = ["<b>📋 Deployment Review</b>\n", "<b>Token Details</b>"]
    lines.append(f"Name: <code>{h(token['name'])}</code>")
    lines.append(f"Symbol: <code>{h(token['symbol'])}</code>")
    lines.append("Supply: <code>1,000,000,000</code> <i>(fixed)</i>")
    lines.append("Decimals: <code>9</code> <i>(fixed)</i>")

    if token.get("description"):
        lines.append(f"Description: <i>{h(token['description'])}</i>")
    if token.get("logo_url"):
        lines.append(f"Logo: {h(token['logo_url'])}")
    if token.get("website"):
        lines.append(f"Website: {h(token['website'])}")
    if token.get("telegram"):
        lines.append(f"Telegram: {h(token['telegram'])}")
    if token.get("twitter"):
        lines.append(f"Twitter: {h(token['twitter'])}")

    lines.append("\n<b>Authority Settings</b>")
    lines.append(f"Revoke Mint: {'✅ Yes' if token.get('revoke_mint') else '❌ No'}")
    lines.append(f"Revoke Freeze: {'✅ Yes' if token.get('revoke_freeze') else '❌ No'}")
    lines.append(f"\n<b>Wallet:</b> <code>{h(wallet_address)}</code>")
    lines.append("<b>Network:</b> Solana Mainnet")
    lines.append("\nReady to launch? Use /launch to continue.")
    return "\n".join(lines)


def launchpad_select_message(name: str, symbol: str) -> str:
    return (
        f"<b>Launch {h(name)}</b> ({h(symbol)})\n\n"
        f"<b>What the bot does after launch:</b>\n\n"
        f"🎯 <b>Auto Market Cap Push</b> — Set a target and the bot monitors price every 30 seconds. "
        f"When your target is hit, it auto-sells your creator tokens to lock in gains.\n\n"
        f"📣 <b>Community Shill Engine</b> — Your token gets pushed to active Solana trading communities "
        f"and listed on DEX Screener for early visibility and volume.\n\n"
        f"─────────────────\n"
        f"Choose your launchpad:"
    )


def creator_buy_message(launchpad: str, balance: float) -> str:
    lp_name = "Pump.fun" if launchpad == "pumpfun" else "Raydium"
    return (
        f"<b>Creator Buy</b>\n\n"
        f"Launchpad: <b>{lp_name}</b>\n"
        f"Wallet balance: <code>{balance:.4f} SOL</code>\n\n"
        f"How much SOL do you want to invest as the creator?\n"
        f"<i>This buys your own token on launch.</i>"
    )


def target_mcap_message(creator_buy_sol: float) -> str:
    buy_str = f"<code>{creator_buy_sol} SOL</code>" if creator_buy_sol > 0 else "<i>none</i>"
    return (
        f"<b>🎯 Set Your Market Cap Target</b>\n\n"
        f"Creator buy: {buy_str}\n\n"
        f"At what market cap should the bot auto-sell all your creator tokens?\n\n"
        f"<i>The bot monitors price every 30 seconds. Once your target is hit, it sells everything instantly.</i>"
    )


def dex_options_message(
    prices: dict,
    balance: float,
    creator_buy_sol: float,
    target_mcap: float,
    dex_update: bool,
    dex_boost: bool,
) -> str:
    mcap_str = f"${int(target_mcap):,}" if target_mcap > 0 else "No auto-sell"
    sol_usd = prices["sol_usd"]
    platform_sol = PLATFORM_FEE_USD / sol_usd
    upd_sol = prices["update_sol"] if dex_update else 0.0
    bst_sol = prices["boost_sol"] if dex_boost else 0.0
    total_sol = 0.05 + platform_sol + creator_buy_sol + upd_sol + bst_sol
    total_usd = total_sol * sol_usd

    lines = [
        "<b>DEX Screener Options</b> <i>(optional)</i>\n",
        f"Creator buy: <code>{creator_buy_sol} SOL</code>" if creator_buy_sol > 0 else "Creator buy: <i>none</i>",
        f"Auto-sell at: <code>{mcap_str}</code>",
        f"Wallet: <code>{balance:.4f} SOL</code>\n",
        f"<b>DEX Update</b> — <code>{prices['update_sol']:.4f} SOL</code> (${DEX_UPDATE_USD})",
        "<i>Adds your token info to DEX Screener</i>\n",
        f"<b>DEX Boost</b> — <code>{prices['boost_sol']:.4f} SOL</code> (${DEX_BOOST_USD})",
        "<i>Boosts your token to the trending section</i>\n",
        f"<i>SOL rate: ${sol_usd:.2f}/SOL</i>\n",
        "<b>── Total Cost ──</b>",
        f"Token creation + fees: <code>0.0500 SOL</code>",
        f"Platform fee: <code>{platform_sol:.4f} SOL</code> (${PLATFORM_FEE_USD})",
    ]
    if creator_buy_sol > 0:
        lines.append(f"Creator buy: <code>{creator_buy_sol:.4f} SOL</code>")
    if dex_update:
        lines.append(f"DEX Update: <code>{upd_sol:.4f} SOL</code> (${DEX_UPDATE_USD})")
    if dex_boost:
        lines.append(f"DEX Boost: <code>{bst_sol:.4f} SOL</code> (${DEX_BOOST_USD})")
    lines.append(f"<b>Total: <code>{total_sol:.4f} SOL</code> (~${total_usd:.0f})</b>")
    return "\n".join(lines)


def insufficient_funds_message(balance: float, required: float) -> str:
    needed = required - balance
    return (
        f"<b>⚠️ Insufficient Funds</b>\n\n"
        f"<b>Current balance:</b> <code>{balance:.4f} SOL</code>\n"
        f"<b>Required:</b> <code>{required:.4f} SOL</code>\n"
        f"<b>Still needed:</b> <code>{needed:.4f} SOL</code>\n\n"
        f"Deposit SOL to your wallet, then use /wallet to verify and /launch to try again."
    )


def deploying_message(launchpad: str) -> str:
    lp = "Pump.fun" if launchpad == "pumpfun" else "Raydium"
    return (
        f"<b>🚀 Deploying on {lp}...</b>\n\n"
        f"This may take 30–60 seconds. Please wait."
    )


def pumpfun_success_message(
    mint_address: str,
    tx_signature: str,
    view_url: str,
    timestamp: str,
    creator_buy_sol: float,
    target_mcap_usd: float,
) -> str:
    short_tx = f"{tx_signature[:16]}..."
    lines = [
        "<b>🟣 Token Live on Pump.fun</b> 🚀\n",
        f"<b>Mint Address</b>\n<code>{h(mint_address)}</code>\n",
        f"<b>Transaction</b>\n<code>{short_tx}</code>\n",
        f"<b>Pump.fun Page</b>\n{h(view_url)}\n",
        f"<b>Status:</b> ✅ Confirmed",
        f"<b>Time:</b> {h(timestamp)}",
    ]
    if creator_buy_sol > 0:
        lines.append(f"\n<b>Creator Buy:</b> <code>{creator_buy_sol} SOL</code> invested")
    if target_mcap_usd > 0:
        lines.append(
            f"\n<b>Auto-Sell Target:</b> <code>${int(target_mcap_usd):,}</code> — "
            "the bot monitors every 30s and will notify you when hit."
        )
    lines.append("\nUse /panel to manage your token.")
    return "\n".join(lines)


def raydium_success_message(
    mint_address: str,
    tx_signature: str,
    timestamp: str,
    target_mcap_usd: float,
) -> str:
    short_tx = f"{tx_signature[:16]}..."
    lines = [
        "<b>🔵 Token Created for Raydium</b> 🚀\n",
        f"<b>Mint Address</b>\n<code>{h(mint_address)}</code>\n",
        f"<b>Transaction</b>\n<code>{short_tx}</code>\n",
        f"<b>Status:</b> ✅ Confirmed",
        f"<b>Time:</b> {h(timestamp)}\n",
        "<b>Next Step:</b>\nGo to <a href=\"https://raydium.io/liquidity/create-pool/\">raydium.io</a> to create a liquidity pool.",
    ]
    if target_mcap_usd > 0:
        lines.append(
            f"\n<b>Auto-Sell Target:</b> <code>${int(target_mcap_usd):,}</code> — "
            "the bot monitors DEX Screener every 30s."
        )
    lines.append("\nUse /panel to manage your token.")
    return "\n".join(lines)


def panel_message(mint_address: str, symbol: str, ui_balance: float) -> str:
    return (
        f"<b>🎛 Token Control Panel</b>\n\n"
        f"<b>Token:</b> <code>{h(symbol)}</code>\n"
        f"<b>Mint:</b> <code>{h(mint_address)}</code>\n"
        f"<b>Balance:</b> <code>{ui_balance:,.2f} {h(symbol)}</code>\n\n"
        f"Choose an action:"
    )


def burn_confirm_message(symbol: str, ui_amount: float, portion: str) -> str:
    label = "half" if portion == "half" else "ALL"
    return (
        f"<b>🔥 Confirm Burn</b>\n\n"
        f"Burn <b>{label}</b> of your <code>{h(symbol)}</code> tokens.\n\n"
        f"Amount: <code>{ui_amount:,.4f} {h(symbol)}</code>\n\n"
        f"⚠️ <b>This is irreversible.</b>"
    )


def revoke_confirm_message(authority_type: str, symbol: str) -> str:
    label = "Mint" if authority_type == "mint" else "Freeze"
    action = "mint new tokens" if authority_type == "mint" else "freeze token accounts"
    return (
        f"<b>🔒 Confirm Revoke {label} Authority</b>\n\n"
        f"Token: <code>{h(symbol)}</code>\n\n"
        f"⚠️ <b>This is permanent and cannot be undone.</b>\n\n"
        f"No one will ever be able to {action} again."
    )


def withdraw_review_message(to_address: str, amount: float, balance: float) -> str:
    return (
        f"<b>📤 Withdrawal Review</b>\n\n"
        f"<b>To:</b> <code>{h(to_address)}</code>\n"
        f"<b>Amount:</b> <code>{amount} SOL</code>\n"
        f"<b>Current Balance:</b> <code>{balance:.4f} SOL</code>\n"
        f"<b>Remaining After:</b> <code>{balance - amount:.4f} SOL</code>\n\n"
        f"Confirm to send."
    )


def withdraw_success_message(to_address: str, amount: float, tx_sig: str) -> str:
    short_tx = f"{tx_sig[:16]}..."
    return (
        f"<b>✅ Withdrawal Sent</b>\n\n"
        f"<b>To:</b> <code>{h(to_address)}</code>\n"
        f"<b>Amount:</b> <code>{amount} SOL</code>\n"
        f"<b>Transaction:</b> <code>{short_tx}</code>\n"
        f"<b>Status:</b> Confirmed"
    )


def error_message(reason: str) -> str:
    return f"<b>❌ Error</b>\n\n{h(reason)}\n\n<i>Use /reset to start over.</i>"


def deposit_notification_message(deposited: float, new_balance: float, wallet: str) -> str:
    status = (
        "✅ You have enough SOL. Use /launch when ready."
        if new_balance >= 2.0
        else f"⚠️ Minimum 2 SOL required. Still need <code>{2.0 - new_balance:.4f} SOL</code>."
    )
    return (
        f"<b>💰 Deposit Received</b>\n\n"
        f"<b>Amount:</b> <code>+{deposited:.4f} SOL</code>\n"
        f"<b>New Balance:</b> <code>{new_balance:.4f} SOL</code>\n"
        f"<b>Wallet:</b> <code>{h(wallet)}</code>\n\n"
        f"{status}"
    )


def mcap_alert_message(mint_address: str, current_mcap: float, target_mcap: float, symbol: str) -> str:
    return (
        f"<b>🎯 Market Cap Target Hit!</b>\n\n"
        f"<b>Token:</b> <code>{h(symbol)}</code>\n"
        f"<b>Mint:</b> <code>{h(mint_address)}</code>\n"
        f"<b>Current Market Cap:</b> <code>${current_mcap:,.0f}</code>\n"
        f"<b>Your Target:</b> <code>${target_mcap:,.0f}</code>\n\n"
        f"Use /panel to sell your tokens now."
    )


def mcap_autosell_message(mint_address: str, tx_sig: str, mcap: float, symbol: str) -> str:
    short_tx = f"{tx_sig[:16]}..."
    return (
        f"<b>✅ Auto-Sell Executed!</b>\n\n"
        f"<b>Token:</b> <code>{h(symbol)}</code>\n"
        f"<b>Market Cap:</b> <code>${mcap:,.0f}</code>\n"
        f"<b>Transaction:</b> <code>{short_tx}</code>\n\n"
        f"All creator tokens sold successfully."
    )
