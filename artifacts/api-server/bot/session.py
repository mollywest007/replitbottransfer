from typing import Any

REQUIRED_FIELDS = ["name", "symbol"]
REQUIRED_PROMPTS = {
    "name": "What is your <b>token name</b>?\n\nExample: <code>Solana Gold</code>",
    "symbol": "What is your <b>token symbol</b>?\n\nExample: <code>SGOLD</code> (2–10 chars, uppercase)",
}

OPTIONAL_FIELDS = ["description", "logo_url", "website", "telegram", "twitter"]
OPTIONAL_PROMPTS = {
    "description": "<b>Token Description</b> (optional)\n\nSend a short description or tap <b>Skip</b>.",
    "logo_url": "<b>Token Logo</b> (optional)\n\nSend an image or paste a direct image URL, or tap <b>Skip</b>.",
    "website": "<b>Website</b> (optional)\n\nSend your project URL or tap <b>Skip</b>.",
    "telegram": "<b>Telegram</b> (optional)\n\nSend your Telegram group/channel link or tap <b>Skip</b>.",
    "twitter": "<b>Twitter/X</b> (optional)\n\nSend your Twitter handle or URL, or tap <b>Skip</b>.",
}


def default_session() -> dict[str, Any]:
    return {
        "step": "idle",
        "collecting_field": None,
        "required_index": 0,
        "optional_index": 0,
        "token": {
            "name": None,
            "symbol": None,
            "supply": 1_000_000_000,
            "decimals": 9,
            "description": None,
            "logo_url": None,
            "website": None,
            "telegram": None,
            "twitter": None,
            "revoke_mint": False,
            "revoke_freeze": False,
        },
        "withdraw": {},
        "panel_transfer": {},
        "history": [],
        "dex_update": False,
        "dex_boost": False,
        "launchpad": None,
        "creator_buy_amount_sol": 0.0,
        "target_market_cap_usd": 0.0,
        "last_mint": None,
        "last_symbol": None,
        "last_decimals": None,
        "pending_burn_portion": None,
        "pending_burn_raw": 0,
        "pending_revoke_type": None,
    }


def get_session(context) -> dict[str, Any]:
    if "session" not in context.user_data:
        context.user_data["session"] = default_session()
    return context.user_data["session"]


def reset_session(context) -> dict[str, Any]:
    context.user_data["session"] = default_session()
    return context.user_data["session"]
