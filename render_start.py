
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
    for name in required("KICK_ACCOUNT_NAMES").split(",")
    if name.strip()
]

tokens = [
    token.strip()
    for token in required("KICK_TOKENS").split(",")
    if token.strip()
]

if len(account_names) != len(tokens):
    raise RuntimeError(
        "KICK_ACCOUNT_NAMES and KICK_TOKENS must have the same number of entries"
    )

streamers = [
    s.strip()
    for s in required("KICK_STREAMERS").split(",")
    if s.strip()
]

if not streamers:
    raise RuntimeError("KICK_STREAMERS must contain a username")

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
        for name, token in zip(account_names, tokens)
    ],
    "Check_interval": 120,
    "Reconnect_cooldown": 600,
    "Connection_stagger_min": 3,
    "Connection_stagger_max": 8,
}

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

sys.exit(subprocess.call([sys.executable, "main.py"]))
