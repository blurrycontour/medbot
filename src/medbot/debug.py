import logging
from telegram import Update
from telegram.ext import ContextTypes

from .db import db

logger = logging.getLogger(__name__)

async def info(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """ Debug command handler - admin only """
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"[MY INFO]\n" \
        f"User ID: {user_id}\n" \
        f"Message ID: {update.message.message_id}\n" \
        f"Chat ID: {update.effective_chat.id}"
    )


async def user_list(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """ List all users command handler - admin only """
    try:
        users = list(db.get_users())
        user_count = len(users)
        user_list_text = "\n".join(
            [f"@{user.get('username', 'N/A')}\n  ID: {user['user_id']}\n  Name: {user.get('first_name', 'N/A')} {user.get('last_name', '')}" for user in users]
        )
        await update.message.reply_text(
            f"[USER LIST] Total Users: {user_count}\n\n{user_list_text}"
        )
    except Exception as e:
        logger.error("Failed to retrieve user list: %s", e)
        await update.message.reply_text("Failed to retrieve user list.")
