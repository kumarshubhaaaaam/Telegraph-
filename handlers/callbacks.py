import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from config import TELEGRAPH_ACCESS_TOKEN, TELEGRAPH_SHORT_NAME
from image_processor import cleanup_files, upload_all_images
from telegraph_client import TelegraphManager
from utils import sessions

logger = logging.getLogger(__name__)

_telegraph_manager: Optional[TelegraphManager] = None


def get_telegraph_manager() -> TelegraphManager:
    """Lazily create a single shared Telegraph account/manager."""
    global _telegraph_manager
    if _telegraph_manager is None:
        _telegraph_manager = TelegraphManager(TELEGRAPH_SHORT_NAME, TELEGRAPH_ACCESS_TOKEN)
    return _telegraph_manager


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    session = sessions.get(user_id)
    await query.answer()

    if query.data == "article_cancel":
        session.reset()
        await query.edit_message_text("❌ Cancelled. All images discarded.")
        return

    if query.data != "article_done":
        return

    if not session.active:
        await query.edit_message_text("No active session. Use /newarticle to start.")
        return

    if not session.images:
        await query.edit_message_text(
            "You haven't sent any images yet. Send some, then tap ✅ Done."
        )
        return

    if session.processing:
        return
    session.processing = True

    total = len(session.images)
    image_paths = list(session.images)  # snapshot, in order
    status_msg = await query.edit_message_text(f"Uploading image 0/{total}...")

    async def progress(done: int, done_total: int) -> None:
        try:
            await status_msg.edit_text(f"Uploading image {done}/{done_total}...")
        except Exception:
            pass  # edits can hit Telegram's rate limit; safe to ignore

    try:
        uploaded = await upload_all_images(image_paths, progress_callback=progress)
        urls = [u for u in uploaded if u]

        if not urls:
            await status_msg.edit_text("❌ All uploads failed. Please try again.")
            return

        await status_msg.edit_text("Creating Telegraph article...")
        manager = get_telegraph_manager()
        article_url = manager.create_article(urls)

        skipped = len(uploaded) - len(urls)
        note = f"\n\n⚠️ {skipped} image(s) were skipped after repeated upload failures." if skipped else ""

        await status_msg.edit_text(
            f"✅ Article Created Successfully\n\n📄 Telegraph:\n{article_url}{note}"
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to create article for user %s", user_id)
        await status_msg.edit_text(f"❌ Something went wrong: {exc}")
    finally:
        cleanup_files(image_paths)
        sessions.clear(user_id)
