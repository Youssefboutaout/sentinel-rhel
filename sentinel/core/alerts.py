import urllib.request
import urllib.parse
import json
import yaml
import os

CONFIG_PATH = "/etc/sentinel/config.yaml"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"telegram": {"enabled": False}}
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {"telegram": {"enabled": False}}

def send_alert(message: str, level: str = "INFO") -> bool:
    """Send an instant notification message to Telegram if enabled."""
    config = load_config()
    tg_conf = config.get("telegram", {})
    
    if not tg_conf.get("enabled", False):
        return False

    token = tg_conf.get("bot_token")
    chat_id = tg_conf.get("chat_id")
    
    if not token or not chat_id or token == "YOUR_BOT_TOKEN_HERE":
        return False

    emoji = "ℹ️"
    if level == "WARNING":
        emoji = "⚠️"
    elif level == "CRITICAL" or level == "HEAL":
        emoji = "🚨"

    formatted_msg = f"{emoji} [Sentinel-RHEL] [{level}]\n\n{message}"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": formatted_msg
    }

    try:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
        return False
