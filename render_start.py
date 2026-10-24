
import json
import os
import subprocess
import sys


def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# Comma-separated account names and tokens
account_names = [
    name.strip()
    for name in required("KICK_ALIAS").split(",")
    if name.strip()
]

tokens = [
    token.strip()
    for token in required("KICK_TOKENS").split(",")
    if token.strip()
]

if len(account_names) != len(tokens):
    raise RuntimeError(
        "KICK_ALIAS and KICK_TOKENS must have the same number of entries"
    )

# Each account gets its own streamer list.
# Use | to separate accounts and commas to separate streamers.
streamer_groups = [
    [s.strip() for s in group.split(",") if s.strip()]
    for group in required("KICK_STREAMERS").split("|")
]

if len(streamer_groups) != len(account_names):
    raise RuntimeError(
        "KICK_STREAMERS must contain one streamer group per account, "
        "separated by |"
    )

if any(not group for group in streamer_groups):
    raise RuntimeError(
        "Every account must have at least one streamer"
    )

config = {
    "Language": os.getenv("LANGUAGE", "en"),
    "Debug": False,
    "WebDashboard": {
        "enabled": True,
        "port": int(os.getenv("PORT", "10000")),
    },
    "Telegram": {
        "enabled": False,
        "bot_token": "",
        "chat_id": "",
        "allowed_users": [],
    },
    "Accounts": [
        {
            "alias": name,
            "token": token,
            "proxy": None,
            "streamers": streamers,
            "max_concurrent": int(
                os.getenv("MAX_CONCURRENT", "2")
            ),
        }
        for name, token, streamers in zip(
            account_names, tokens, streamer_groups
        )
    ],
    "Check_interval": 120,
    "Reconnect_cooldown": 600,
    "Connection_stagger_min": 3,
    "Connection_stagger_max": 8,
}

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

sys.exit(subprocess.call([sys.executable, "main.py"]))
