import json
import os

CONFIG_DIR = os.path.expanduser("~/.config/traypresso")
CONFIG_PATH = os.path.join(CONFIG_DIR, "settings.json")

DEFAULTS = {
    "custom_duration_mode": False,
    "last_duration_minutes": 10,  # None means Indefinite
    "ignore_lid": False,
}


def load_settings() -> dict:
    try:
        with open(CONFIG_PATH) as f:
            return {**DEFAULTS, **json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def save_settings(data: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)
