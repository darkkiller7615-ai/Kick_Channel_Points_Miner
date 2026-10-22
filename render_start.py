
import json
import os
import subprocess
import sys

def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

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
            "alias": os.getenv("KICK_ALIAS", "Main Account"),
            "token": required("KICK_TOKEN"),
            "proxy": None,
            "streamers": [
                s.strip()
                for s in required("KICK_STREAMERS").split(",")
                if s.strip()
            ],
            "max_concurrent": int(
                os.getenv("MAX_CONCURRENT", "2")
            ),
        }
    ],
    "Check_interval": 120,
    "Reconnect_cooldown": 600,
    "Connection_stagger_min": 3,
    "Connection_stagger_max": 8,
}

if not config["Accounts"][0]["streamers"]:
    raise RuntimeError("KICK_STREAMERS must contain a username")

with open("config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

sys.exit(subprocess.call([sys.executable, "main.py"]))
