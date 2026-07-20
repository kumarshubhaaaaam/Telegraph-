"""
Main entry point. Run this directly for local development / any host that
supports long-running processes with outbound polling (e.g. a Render
"Background Worker", or your own VPS).

For Render "Web Service" free-tier deployments, which require the app to
bind to a port, use server.py instead (webhook mode via FastAPI).
"""
import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from handlers.callbacks import handle_callback
from handlers.commands import newarticle, start
from handlers.images import handle_photo

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newarticle", newarticle))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_callback))

    return app


def main() -> None:
    app = build_application()
    logger.info("Bot starting in polling mode...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
