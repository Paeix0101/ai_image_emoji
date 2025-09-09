from flask import Flask, request
import os
import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Missing BOT_TOKEN environment variable")

WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", BOT_TOKEN)
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_URL = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

WELCOME_MSG = "<i>🖼 Image → Emoji Converter\n\nJust send me an image and I will make it tiny like an emoji!</i>"

def send_message(chat_id, text):
    requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def send_photo(chat_id, file_bytes):
    files = {"photo": ("emoji.png", file_bytes)}
    requests.post(f"{API_URL}/sendPhoto", data={"chat_id": chat_id}, files=files)

@app.route(f"/{WEBHOOK_PATH}", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        return "ok"

    msg = data.get("message") or {}
    chat_id = msg.get("chat", {}).get("id")

    # /start command
    if msg.get("text", "").startswith("/start"):
        send_message(chat_id, WELCOME_MSG)
        return "ok"

    # Handle photos
    if "photo" in msg:
        # Get highest resolution photo
        photo = msg["photo"][-1]
        file_id = photo["file_id"]

        # Get file path
        r = requests.get(f"{API_URL}/getFile?file_id={file_id}")
        file_path = r.json()["result"]["file_path"]

        # Download file
        img_data = requests.get(f"{FILE_URL}/{file_path}").content

        # Resize image to tiny emoji-like size
        img = Image.open(BytesIO(img_data))
        img = img.convert("RGBA")
        img = img.resize((32, 32))  # make it tiny

        # Save to memory
        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)

        # Send back resized image
        send_photo(chat_id, output)

    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
