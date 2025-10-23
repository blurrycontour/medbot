import logging
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import datetime
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import ContextTypes

from .db import db

logger = logging.getLogger(__name__)
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Start command handler """
    # Create a user entry if not exists
    user = update.effective_user
    db.users.update_one(
        {'user_id': user.id},
        {'$set': {
            'user_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username
        }},
        upsert=True
    )
    # Notify admin of new user
    admin_user_id = os.getenv("ADMIN_USER_ID")
    if admin_user_id:
        try:
            await context.bot.send_message(
                chat_id=int(admin_user_id),
                text=f"[INFO] New user started the bot:\n"
                     f"ID: {user.id}\n"
                     f"Name: {user.full_name}\n"
                     f"Username: @{user.username if user.username else 'N/A'}"
            )
        except Exception as e:
            logger.error("Failed to notify admin of new user: %s", e)

    await update.message.reply_text(
        "Hej! I'm very friendly MedBot 🤖!\n" \
        "I can send medication reminders at a time you choose.\n\n" \
        "I'll try to detect your timezone — send your location OR set it manually with\n/timezone <Region/City> (e.g. /timezone Europe/London)"
    )


async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Set a reminder """
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    tz_name = user.get('tz')

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /set <HH:MM> <medicine-name>")
        return
    if not tz_name:
        await update.message.reply_text("Please set your timezone first using /timezone command")
        return
    try:
        reminder_time = datetime.strptime(context.args[0], "%H:%M").time()
        name = " ".join(context.args[1:]).strip()
        # add a reminder document for this user
        db.add_reminder({
            'user_id': user_id,
            'time': reminder_time.strftime("%H:%M"),
            'name': name,
            'confirmed': False,
            'last_sent_date': None
        })
        await update.message.reply_text(f"Reminder set for '{name}' at {reminder_time.strftime('%H:%M')}")
    except ValueError:
        await update.message.reply_text("Invalid time format. Use HH:MM.")


async def settz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Set timezone command handler """
    user_id = update.effective_user.id
    # If user provided tz string as arg, try to validate
    if len(context.args) == 1:
        tz_name = context.args[0]
        try:
            ZoneInfo(tz_name) # validate via ZoneInfo
            # upsert tz only
            db.users.update_one({'user_id': user_id}, {'$set': {'tz': tz_name}}, upsert=True)
            await update.message.reply_text(f"Timezone set to {tz_name}")
        except ZoneInfoNotFoundError:
            await update.message.reply_text("Invalid timezone!\nUse an IANA timezone like 'Europe/London'.")
        return

    # No args: prompt for location
    kb = [[KeyboardButton(text="Share location", request_location=True)]]
    await update.message.reply_text(
        "Please share your location so I can detect your timezone, OR use /timezone <Region/City>",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
    )


async def list_reminders(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """ List reminders command handler """
    user_id = update.effective_user.id
    try:
        reminders = list(db.get_reminders(user_id))
        if not reminders:
            await update.message.reply_text("No reminders set\nUse /set to add one")
            return
        msg_lines = ["Your reminders:"]
        max_line_len = 0
        for r in reminders:
            time_str = r.get('time')
            name = r.get('name')
            streak = r.get('streak', 0)
            streak_txt = f"    🔥 {streak} day{'s' if streak > 1 else ''}" if streak else ""
            msg_line = f"⏰ {time_str} - {name}{streak_txt}"
            msg_lines.append(msg_line)
            if len(msg_line) > max_line_len:
                max_line_len = len(msg_line)
        # pad the message lines for better readability
        msg_lines = [msg_lines[0]] + [line.ljust(max_line_len) for line in msg_lines[1:]]

        await update.message.reply_text("\n".join(msg_lines))

    except ValueError:
        await update.message.reply_text("Error retrieving reminders")


async def remove_reminder(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """ Remove reminder command handler """
    user_id = update.effective_user.id
    try:
        reminders = list(db.get_reminders(user_id))
        if not reminders:
            await update.message.reply_text("No reminders set\nUse /set to add one")
            return
        # give user list of reminders as keyboard buttons to choose from
        kb = []
        for r in reminders:
            rid = str(r.get('_id'))  # use document id to identify the reminder reliably
            label = f"⏰ {r.get('time')} - {r.get('name')}"
            kb.append([InlineKeyboardButton(text=label, callback_data=f"remove:{rid}")])
        kb.append([InlineKeyboardButton(text="[All Reminders]", callback_data="remove:all")])
        kb.append([InlineKeyboardButton(text="[Cancel]", callback_data="remove:cancel")])

        await update.message.reply_text(
            "Select a reminder to remove:",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    except ValueError:
        await update.message.reply_text("Error removing reminders")


async def user_stats(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """ User stats command handler """
    user_id = update.effective_user.id
    try:
        reminders = list(db.get_reminders(user_id))
        if not reminders:
            await update.message.reply_text("No reminders set\nUse /set to add one")
            return
        total_reminders = len(reminders)
        longest_streak = max((r.get('streak', 0) for r in reminders), default=0)

        stats_msg = (
            f"📊 Your Stats:\n"
            f"Total Reminders: {total_reminders}\n"
            f"Longest Streak: {longest_streak} day{'s' if longest_streak != 1 else ''} 🔥\n\n"
            "Keep up the good work! 💪💊"
        )
        await update.message.reply_text(stats_msg)

    except ValueError:
        await update.message.reply_text("Error retrieving user stats")


async def help_command(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """ Help command handler """
    help_text = (
        "Available commands:\n"
        "/start - Get started with the bot\n"
        "/timezone - Set your timezone\n"
        "/set - Create a new reminder\n"
        "/list - List all your reminders\n"
        "/stats - Your statistics\n"
        "/remove - Remove a reminder or all reminders\n"
        "/help - Show this help message"
    )
    if ADMIN_USER_ID and update.effective_user.id == int(ADMIN_USER_ID):
        help_text += "\n\nAdmin commands:\n"
        help_text += "/info - Get my user info\n"
        help_text += "/users - List all users\n"
        help_text += "/sudolist - List reminders for a specific user\n"
    await update.message.reply_text(help_text)
