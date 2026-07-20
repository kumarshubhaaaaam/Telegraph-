"""
Optional webhook entry point for platforms (like Render's free "Web
Service" tier) that require the app to bind to a port rather than run a
long-lived polling loop.

Run with:  uvicorn server:app --host 0.0.0.0 --port $PORT
"""
import logging

from fastapi import FastAPI, Request
from telegram import Update

from bot import build_application
from config import PORT, WEBHOOK_BASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/webhook"

app = FastAPI()
telegram_app = build_application()


@app.on_event("startup")
async def on_startup() -> None:
    await telegram_app.initialize()
    await telegram_app.start()
    if WEBHOOK_BASE_URL:
        url = f"{WEBHOOK_BASE_URL.rstrip('/')}{WEBHOOK_PATH}"
        await telegram_app.bot.set_webhook(url=url)
        logger.info("Webhook set to %s", url)
    else:
        logger.warning(
            "WEBHOOK_BASE_URL / RENDER_EXTERNAL_URL not set — webhook was NOT registered with Telegram."
        )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await telegram_app.stop()
    await telegram_app.shutdown()


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> dict:
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


@app.get("/")
async def health() -> dict:
    return {"status": "running", "port": PORT}
