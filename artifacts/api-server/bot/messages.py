from config import DEPLOYMENT_FEE, PLATFORM_FEE_USD, DEX_UPDATE_USD, DEX_BOOST_USD


def escape(text: str) -> str:
    for ch in r"\*_[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


def main_menu_message() -> str:
    return (
        "*TokenLaunchBot* — Solana SPL Token Deployer\n\n"
        "Deploy tokens on Solana in minutes\\.\n\n"
        "*Commands*\n"
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
        f"*💼 Deployment Wallet*\n\n"
        f"*Address*\n`{address}`\n\n"
        f"*Balance*\n`{balance:.4f} SOL` — {enough}\n\n"
        f"*Minimum Required*\n`{DEPLOYMENT_FEE} SOL`\n\n"
        f"*Private Key*\n`{status}`\n\n"
        f"*Network*\nSolana Mainnet\n\n"
        f"_This is a fixed deployment wallet\\._"
    )


def help_message() -> str:
    return (
        f"*TokenLaunchBot Help*\n\n"
        f"*Supported Network:* Solana \\(SPL Tokens\\)\n\n"
        f"*Minimum Wallet Balance:* `{DEPLOYMENT_FEE} SOL`\n"
        f"_Covers token creation, creator buy, and all on\\-chain fees\\._\n\n"
        f"*How it works:*\n"
        f"1\\. /create — Enter token details\n"
        f"2\\. /review — Check everything looks right\n"
        f"3\\. /launch — Choose launchpad, set creator buy & market cap target\n"
        f"4\\. /panel — Manage your token after launch\n\n"
        f"*Required fields:* Name, Symbol\n"
        f"*Optional:* Description, Logo, Website, Telegram, Twitter\n\n"
        f"The bot uses a single dedicated deployment wallet\\.\n"
        f"Use /wallet to check your balance\\.\n\n"
        f"*Support*\n"
        f"Contact [@devBernard](https://t\\.me/devBernard) on Telegram\\."
    )


def review_message(token: dict, wallet_address: str) -> str:
    lines = ["*📋 Deployment Review*\n", "*Token Details*"]
    lines.append(f"Name: `{token['name']}`")
    lines.append(f"Symbol: `{token['symbol']}`")
    lines.append("Supply: `1,000,000,000` \\(fixed\\)")
    lines.append("Decimals: `9` \\(fixed\\)")

    if token.get("description"):
        lines.append(f"Description: _{escape(token['description'])}_")
    if token.get("logo_url"):
        lines.append(f"Logo: {token['logo_url']}")
    if token.get("website"):
        lines.append(f"Website: {token['website']}")
    if token.get("telegram"):
        lines.append(f"Telegram: {token['telegram']}")
    if token.get("twitter"):
        lines.append(f"Twitter: {token['twitter']}")

    lines.append("\n*Authority Settings*")
    lines.append(f"Revoke Mint: {'✅ Yes' if token.get('revoke_mint') else '❌ No'}")
    lines.append(f"Revoke Freeze: {'✅ Yes' if token.get('revoke_freeze') else '❌ No'}")

    lines.append(f"\n*Wallet:* `{wallet_address}`")
    lines.append(f"*Network:* Solana Mainnet")
    lines.append("\nReady to launch? Use /launch to continue\\.")
    return "\n".join(lines)


def launchpad_select_message(name: str, symbol: str) -> str:
    return (
        f"*Launch {escape(name)}* \\({escape(symbol)}\\)\n\n"
        f"*What the bot does after launch:*\n\n"
        f"🎯 *Auto Market Cap Push* — Set a target and the bot monitors price every 30 seconds\\. "
        f"When your target is hit, it auto\\-sells your creator tokens to lock in gains\\.\n\n"
        f"📣 *Community Shill Engine* — Your token gets pushed to active Solana trading communities "
        f"and listed on DEX Screener for early visibility and volume\\.\n\n"
        f"─────────────────\n"
        f"Choose your launchpad:"
    )


def creator_buy_message(launchpad: str, balance: float) -> str:
    lp_name = "Pump\\.fun" if launchpad == "pumpfun" else "Raydium"
    return (
        f"*Creator Buy*\n\n"
        f"Launchpad: *{lp_name}*\n"
        f"Wallet balance: `{balance:.4f} SOL`\n\n"
        f"How much SOL do you want to invest as the creator?\n"
        f"_This buys your own token on launch\\._"
    )


def target_mcap_message(creator_buy_sol: float) -> str:
    buy_str = f"`{creator_buy_sol} SOL`" if creator_buy_sol > 0 else "_none_"
    return (
        f"*🎯 Set Your Market Cap Target*\n\n"
        f"Creator buy: {buy_str}\n\n"
        f"At what market cap should the bot auto\\-sell all your creator tokens?\n\n"
        f"_The bot monitors price every 30 seconds\\. Once your target is hit, it sells everything instantly\\._"
    )


def dex_options_message(
    prices: dict,
    balance: float,
    creator_buy_sol: float,
    target_mcap: float,
    dex_update: bool,
    dex_boost: bool,
) -> str:
    mcap_str = f"${int(target_mcap):,}" if target_mcap > 0 else "No auto\\-sell"
    sol_usd = prices["sol_usd"]
    platform_sol = PLATFORM_FEE_USD / sol_usd
    upd_sol = prices["update_sol"] if dex_update else 0.0
    bst_sol = prices["boost_sol"] if dex_boost else 0.0
    total_sol = 0.05 + platform_sol + creator_buy_sol + upd_sol + bst_sol
    total_usd = total_sol * sol_usd

    lines = [
        "*DEX Screener Options* \\(optional\\)\n",
        f"Creator buy: `{creator_buy_sol} SOL`" if creator_buy_sol > 0 else "Creator buy: _none_",
        f"Auto\\-sell at: `{mcap_str}`",
        f"Wallet: `{balance:.4f} SOL`\n",
        f"*DEX Update* — `{prices['update_sol']:.4f} SOL` \\(${DEX_UPDATE_USD}\\)",
        "_Adds your token info to DEX Screener_\n",
        f"*DEX Boost* — `{prices['boost_sol']:.4f} SOL` \\(${DEX_BOOST_USD}\\)",
        "_Boosts your token to the trending section_\n",
        f"_SOL rate: ${sol_usd:.2f}/SOL_\n",
        "*── Total Cost ──*",
        f"Token creation: `0\\.0500 SOL`",
        f"Platform fee: `{platform_sol:.4f} SOL` \\(${PLATFORM_FEE_USD}\\)",
    ]
    if creator_buy_sol > 0:
        lines.append(f"Creator buy: `{creator_buy_sol:.4f} SOL`")
    if dex_update:
        lines.append(f"DEX Update: `{upd_sol:.4f} SOL` \\(${DEX_UPDATE_USD}\\)")
    if dex_boost:
        lines.append(f"DEX Boost: `{bst_sol:.4f} SOL` \\(${DEX_BOOST_USD}\\)")
    lines.append(f"*Total: `{total_sol:.4f} SOL` \\(~${total_usd:.0f}\\)*")
    return "\n".join(lines)


def insufficient_funds_message(balance: float, required: float) -> str:
    needed = required - balance
    return (
        f"*⚠️ Insufficient Funds*\n\n"
        f"*Current balance:* `{balance:.4f} SOL`\n"
        f"*Required:* `{required:.4f} SOL`\n"
        f"*Still needed:* `{needed:.4f} SOL`\n\n"
        f"Deposit SOL to your wallet, then use /wallet to verify and /launch to try again\\."
    )


def deploying_message(launchpad: str) -> str:
    lp = "Pump\\.fun" if launchpad == "pumpfun" else "Raydium"
    return (
        f"*🚀 Deploying on {lp}\\.\\.\\.*\n\n"
        f"This may take 30–60 seconds\\. Please wait\\."
    )


def pumpfun_success_message(
    mint_address: str,
    tx_signature: str,
    view_url: str,
    timestamp: str,
    creator_buy_sol: float,
    target_mcap_usd: float,
) -> str:
    short_tx = f"{tx_signature[:8]}\\.\\.\\."
    lines = [
        "*🟣 Token Live on Pump\\.fun* 🚀\n",
        f"*Mint Address*\n`{mint_address}`\n",
        f"*Transaction*\n`{short_tx}`\n",
        f"*Pump\\.fun Page*\n{view_url}\n",
        f"*Status:* ✅ Confirmed",
        f"*Time:* {timestamp}",
    ]
    if creator_buy_sol > 0:
        lines.append(f"\n*Creator Buy:* `{creator_buy_sol} SOL` invested")
    if target_mcap_usd > 0:
        lines.append(
            f"\n*Auto\\-Sell Target:* `${int(target_mcap_usd):,}` — "
            "the bot monitors every 30s and will notify you when hit\\."
        )
    lines.append("\nUse /panel to manage your token\\.")
    return "\n".join(lines)


def raydium_success_message(
    mint_address: str,
    tx_signature: str,
    timestamp: str,
    target_mcap_usd: float,
) -> str:
    short_tx = f"{tx_signature[:8]}\\.\\.\\."
    lines = [
        "*🔵 Token Created for Raydium* 🚀\n",
        f"*Mint Address*\n`{mint_address}`\n",
        f"*Transaction*\n`{short_tx}`\n",
        f"*Status:* ✅ Confirmed",
        f"*Time:* {timestamp}\n",
        "*Next Step:*\nGo to [raydium\\.io](https://raydium.io/liquidity/create\\-pool/) to create a liquidity pool\\.",
    ]
    if target_mcap_usd > 0:
        lines.append(
            f"\n*Auto\\-Sell Target:* `${int(target_mcap_usd):,}` — "
            "the bot monitors DEX Screener every 30s\\."
        )
    lines.append("\nUse /panel to manage your token\\.")
    return "\n".join(lines)


def panel_message(mint_address: str, symbol: str, ui_balance: float) -> str:
    return (
        f"*🎛 Token Control Panel*\n\n"
        f"*Token:* `{symbol}`\n"
        f"*Mint:* `{mint_address}`\n"
        f"*Balance:* `{ui_balance:,.2f} {symbol}`\n\n"
        f"Choose an action:"
    )


def burn_confirm_message(symbol: str, ui_amount: float, portion: str) -> str:
    label = "half" if portion == "half" else "ALL"
    return (
        f"*🔥 Confirm Burn*\n\n"
        f"Burn *{label}* of your `{symbol}` tokens\\.\n\n"
        f"Amount: `{ui_amount:,.4f} {symbol}`\n\n"
        f"⚠️ *This is irreversible\\.*"
    )


def revoke_confirm_message(authority_type: str, symbol: str) -> str:
    label = "Mint" if authority_type == "mint" else "Freeze"
    action = "mint new tokens" if authority_type == "mint" else "freeze token accounts"
    return (
        f"*🔒 Confirm Revoke {label} Authority*\n\n"
        f"Token: `{symbol}`\n\n"
        f"⚠️ *This is permanent and cannot be undone\\.*\n\n"
        f"No one will ever be able to {action} again\\."
    )


def withdraw_review_message(to_address: str, amount: float, balance: float) -> str:
    return (
        f"*📤 Withdrawal Review*\n\n"
        f"*To:* `{to_address}`\n"
        f"*Amount:* `{amount} SOL`\n"
        f"*Current Balance:* `{balance:.4f} SOL`\n"
        f"*Remaining After:* `{balance - amount:.4f} SOL`\n\n"
        f"Confirm to send\\."
    )


def withdraw_success_message(to_address: str, amount: float, tx_sig: str) -> str:
    short_tx = f"{tx_sig[:8]}\\.\\.\\."
    return (
        f"*✅ Withdrawal Sent*\n\n"
        f"*To:* `{to_address}`\n"
        f"*Amount:* `{amount} SOL`\n"
        f"*Transaction:* `{short_tx}`\n"
        f"*Status:* Confirmed"
    )


def error_message(reason: str) -> str:
    return f"*❌ Error*\n\n{reason}\n\n_Use /reset to start over\\._"


def deposit_notification_message(deposited: float, new_balance: float, wallet: str) -> str:
    status = (
        "✅ You have enough SOL\\. Use /launch when ready\\."
        if new_balance >= 2.0
        else f"⚠️ Minimum 2 SOL required\\. Still need `{2.0 - new_balance:.4f} SOL`\\."
    )
    return (
        f"*💰 Deposit Received*\n\n"
        f"*Amount:* `+{deposited:.4f} SOL`\n"
        f"*New Balance:* `{new_balance:.4f} SOL`\n"
        f"*Wallet:* `{wallet}`\n\n"
        f"{status}"
    )


def mcap_alert_message(mint_address: str, current_mcap: float, target_mcap: float, symbol: str) -> str:
    return (
        f"*🎯 Market Cap Target Hit\\!*\n\n"
        f"*Token:* `{symbol}`\n"
        f"*Mint:* `{mint_address}`\n"
        f"*Current Market Cap:* `${current_mcap:,.0f}`\n"
        f"*Your Target:* `${target_mcap:,.0f}`\n\n"
        f"Use /panel to sell your tokens now\\."
    )


def mcap_autosell_message(mint_address: str, tx_sig: str, mcap: float, symbol: str) -> str:
    short_tx = f"{tx_sig[:8]}\\.\\.\\."
    return (
        f"*✅ Auto\\-Sell Executed\\!*\n\n"
        f"*Token:* `{symbol}`\n"
        f"*Market Cap:* `${mcap:,.0f}`\n"
        f"*Transaction:* `{short_tx}`\n\n"
        f"All creator tokens sold successfully\\."
    )
