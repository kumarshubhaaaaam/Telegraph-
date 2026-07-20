"""
Central configuration, loaded from environment variables / .env file.
"""
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
TELEGRAPH_SHORT_NAME = os.getenv("TELEGRAPH_SHORT_NAME", "ImageBot")
# Optional: reuse the same Telegraph account across restarts instead of
# creating a brand new one every time the process boots.
TELEGRAPH_ACCESS_TOKEN = os.getenv("TELEGRAPH_ACCESS_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

TEMP_DIR = os.getenv("TEMP_DIR", "temp_images")
MAX_IMAGES_PER_ARTICLE = int(os.getenv("MAX_IMAGES_PER_ARTICLE", "200"))
UPLOAD_CONCURRENCY = int(os.getenv("UPLOAD_CONCURRENCY", "5"))
ALBUM_DEBOUNCE_SECONDS = float(os.getenv("ALBUM_DEBOUNCE_SECONDS", "1.5"))

# Webhook mode (optional, used by server.py on Render)
PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_BASE_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_BASE_URL")

_REQUIRED = {"BOT_TOKEN": BOT_TOKEN, "IMGBB_API_KEY": IMGBB_API_KEY}
_missing = [k for k, v in _REQUIRED.items() if not v]
if _missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(_missing)}. "
        f"Copy .env.example to .env and fill in the values."
    )
