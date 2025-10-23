import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
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


async def sudo_list_reminders(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """ List reminders command handler """
    try:
        # give user list of users as keyboard buttons to choose from
        users = list(db.get_users())
        kb = []
        for u in users:
            uid = str(u.get('user_id'))
            username = u.get('username')
            kb.append([InlineKeyboardButton(text=f"@{username}", callback_data=f"sudolist:{uid}")])
        kb.append([InlineKeyboardButton(text="[Cancel]", callback_data="sudolist:cancel")])

        await update.message.reply_text(
            "Select a user:",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    except ValueError:
        await update.message.reply_text("Error retrieving users")
