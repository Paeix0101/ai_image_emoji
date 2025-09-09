from flask import Flask, request
import os
import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("❌ Missing BOT_TOKEN environment variable")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_URL = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

WELCOME_MSG = (
    "<b>🖼️ Image → Emoji Converter</b>\n\n"
    "✨ Just send me any image, and I’ll shrink it into emoji size (64×64).\n"
    "You can then use it like a mini-sticker!"
)

def send_message(chat_id, text, parse_mode="HTML"):
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    })

def send_photo(chat_id, image_bytes):
    """Send processed image back to user"""
    files = {"photo": ("emoji.png", image_bytes, "image/png")}
    requests.post(f"{API_URL}/sendPhoto", data={"chat_id": chat_id}, files=files)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        return "ok"

    msg = data.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")
    photo = msg.get("photo")

    # /start command
    if text and text.strip().lower().startswith("/start"):
        send_message(chat_id, WELCOME_MSG)
        return "ok"

    # Handle photo upload
    if photo:
        # Get highest quality photo
        file_id = photo[-1]["file_id"]
        file_info = requests.get(f"{API_URL}/getFile?file_id={file_id}").json()
        file_path = file_info["result"]["file_path"]

        # Download photo
        img_data = requests.get(f"{FILE_URL}/{file_path}").content
        img = Image.open(BytesIO(img_data))

        # Convert to RGBA & resize to 64x64
        img = img.convert("RGBA")
        img = img.resize((64, 64), Image.LANCZOS)

        # Save into memory
        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)

        # Send back
        send_photo(chat_id, output)

    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

