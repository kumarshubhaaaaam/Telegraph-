from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils import sessions

DONE_CANCEL_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("✅ Done", callback_data="article_done"),
            InlineKeyboardButton("❌ Cancel", callback_data="article_cancel"),
        ]
    ]
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Hi! I turn a batch of images into a single Telegraph article.\n\n"
        "Use /newarticle to begin, then send me your images."
    )


async def newarticle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = sessions.get(user_id)

    if session.active and session.images:
        await update.message.reply_text(
            "You already have an article in progress with "
            f"{len(session.images)} image(s). Send more, tap ✅ Done, "
            "or ❌ Cancel to start over.",
            reply_markup=DONE_CANCEL_KEYBOARD,
        )
        return

    session.start()
    await update.message.reply_text(
        "📸 Send all images (one by one, or as albums).\n\n"
        "When you're finished, tap ✅ Done below.",
        reply_markup=DONE_CANCEL_KEYBOARD,
    )
