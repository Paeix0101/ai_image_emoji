from flask import Flask, request
import os
import requests
from PIL import Image
import io

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Missing BOT_TOKEN environment variable")

WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", "emoji_webhook")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_API = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

# Emojis by brightness (dark → light)
EMOJI_MAP = ["⬛", "🟫", "🟩", "🟨", "🟦", "⬜"]

WELCOME_MSG = "<i>image to emoji converter \n\n just send the image</i>"

def send_message(chat_id: int, text: str, parse_mode: str = "HTML"):
    """Send a message back to Telegram"""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    requests.post(f"{API_URL}/sendMessage", json=payload)

def convert_image_to_emoji(image_bytes):
    """Convert image to emoji mosaic"""
    img = Image.open(io.BytesIO(image_bytes)).convert("L")  # grayscale
    img = img.resize((30, 30))  # shrink for text limits

    emoji_art = ""
    for y in range(img.height):
        row = ""
        for x in range(img.width):
            brightness = img.getpixel((x, y))
            idx = brightness * (len(EMOJI_MAP) - 1) // 255
            row += EMOJI_MAP[idx]
        emoji_art += row + "\n"
    return emoji_art

@app.route(f"/{WEBHOOK_PATH}", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        return "ok"

    msg = data.get("message")
    if not msg:
        return "ok"

    chat_id = msg["chat"]["id"]

    # if /start command
    text = msg.get("text", "")
    if text and text.strip().lower().startswith("/start"):
        send_message(chat_id, WELCOME_MSG, parse_mode="HTML")
        return "ok"

    # if photo message
    if "photo" in msg:
        file_id = msg["photo"][-1]["file_id"]  # largest size
        file_info = requests.get(f"{API_URL}/getFile", params={"file_id": file_id}).json()
        file_path = file_info["result"]["file_path"]

        # download image
        file_url = f"{FILE_API}/{file_path}"
        img_data = requests.get(file_url).content

        # convert to emoji
        emoji_art = convert_image_to_emoji(img_data)

        # send back
        if len(emoji_art) > 4000:  # Telegram message limit
            send_message(chat_id, "⚠️ Emoji art too large, please send a smaller image.")
        else:
            send_message(chat_id, emoji_art)

    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
