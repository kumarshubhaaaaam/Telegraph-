"""
Handles incoming photos, including Telegram albums (media groups).

Ordering note: python-telegram-bot's Application processes updates
sequentially by default (concurrent_updates=False), so photos are handled
in the order Telegram delivers them, which preserves both single-photo and
album order. Do not enable concurrent_updates on the Application without
adding explicit sequence numbers, or album order can no longer be
guaranteed.
"""
import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import ALBUM_DEBOUNCE_SECONDS, MAX_IMAGES_PER_ARTICLE
from utils import sessions

logger = logging.getLogger(__name__)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = sessions.get(user_id)

    if not session.active:
        return  # ignore images sent outside of an active /newarticle session

    if session.processing:
        await update.message.reply_text("⏳ Still processing your last article, please wait.")
        return

    if len(session.images) >= MAX_IMAGES_PER_ARTICLE:
        await update.message.reply_text(
            f"⚠️ Limit of {MAX_IMAGES_PER_ARTICLE} images reached. Tap ✅ Done to finish."
        )
        return

    message = update.message
    photo = message.photo[-1]  # highest available resolution, no compression on our side
    file = await context.bot.get_file(photo.file_id)

    dest_path = session.next_path("jpg")
    await file.download_to_drive(dest_path)
    session.images.append(dest_path)

    if not message.media_group_id:
        await message.reply_text(f"📥 Received image #{len(session.images)}")
        return

    # For albums, debounce so we send one confirmation instead of spamming
    # a reply per photo in the group.
    key = f"{user_id}:{message.media_group_id}"
    pending = context.chat_data.setdefault("_album_ack_pending", set())
    if key in pending:
        return
    pending.add(key)

    async def _ack() -> None:
        await asyncio.sleep(ALBUM_DEBOUNCE_SECONDS)
        pending.discard(key)
        try:
            await message.reply_text(f"📥 Received {len(session.images)} image(s) so far")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send album ack: %s", exc)

    asyncio.create_task(_ack())
