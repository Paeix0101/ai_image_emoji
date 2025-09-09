from flask import Flask, request
import os
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Missing BOT_TOKEN environment variable")

WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", BOT_TOKEN)
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

START_MSG = (
    "<b>Image ➝ Emoji Converter ✨</b>\n\n"
    "<i>Just send me an image and I’ll shrink it into emoji-style size!</i>"
)

def send_message(chat_id: int, text: str, parse_mode: str = "HTML"):
    """Send a message via Telegram sendMessage."""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    try:
        requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
    except Exception:
        pass  # ignore network errors so webhook won’t crash


# ✅ Circle Tick Helper
def get_circle_tick(color: str = "blue") -> str:
    """Return a circle with a tick combo."""
    if color == "blue":
        return "🔵✔️"
    elif color == "green":
        return "🟢✔️"
    elif color == "white":
        return "⚪✔️"
    elif color == "black":
        return "⚫✔️"
    else:
        return "✔️"  # fallback


@app.route(f"/{WEBHOOK_PATH}", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        return "ok"

    msg = data.get("message") or data.get("edited_message")
    if not msg:
        return "ok"

    text = msg.get("text", "") or ""
    chat_id = msg.get("chat", {}).get("id")

    # /start
    if text and text.strip().lower().startswith("/start") and chat_id:
        send_message(chat_id, START_MSG, parse_mode="HTML")

    # /verified → send blue tick
    if text and text.strip().lower().startswith("/verified") and chat_id:
        tick = get_circle_tick("blue")
        send_message(chat_id, f"This user is verified {tick}", parse_mode="HTML")

    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
