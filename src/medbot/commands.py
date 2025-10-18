import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from .db import db

logger = logging.getLogger(__name__)


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to MedBot!\n\n" \
        "I can send medication reminders at a time you choose.\n\n" \
        "I try to detect your timezone automatically — you can send your location OR set it manually with /timezone <Region/City> (e.g. /timezone Europe/London)."
    )


async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /set <HH:MM>")
        return
    try:
        reminder_time = datetime.strptime(context.args[0], "%H:%M").time()
        # ensure user document exists (preserve tz if present)
        existing = db.users.find_one({'user_id': user_id}) or {}
        # upsert user document with existing tz if present
        db.users.update_one({'user_id': user_id}, {'$set': {'tz': existing.get('tz')}}, upsert=True)
        # add a reminder document for this user
        res = db.reminders.insert_one({
            'user_id': user_id,
            'time': reminder_time.strftime("%H:%M"),
            'confirmed': 0,
            'last_sent_date': None
        })
        rid = str(res.inserted_id)
        # If we don't have a timezone yet, ask user to set or share location
        user = db.users.find_one({'user_id': user_id}) or {}
        if not user.get('tz'):
            kb = [[KeyboardButton(text="Share location", request_location=True)]]
            await update.message.reply_text(
                "Reminder set, but I don't know your timezone. Please run /timezone or /timezone <Region/City>",
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
            )
            return
        await update.message.reply_text(f"Reminder set for {reminder_time.strftime('%H:%M')}")
    except ValueError:
        await update.message.reply_text("Invalid time format. Use HH:MM.")


async def settz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set timezone manually (/timezone Region/City) or ask user to share location.
    If user sends /timezone with no args, bot will prompt for location permission button."""
    user_id = update.effective_user.id
    # If user provided tz string as arg, try to validate
    if len(context.args) == 1:
        tz_name = context.args[0]
        try:
            # validate by creating ZoneInfo
            ZoneInfo(tz_name)
            # upsert tz only
            db.users.update_one({'user_id': user_id}, {'$set': {'tz': tz_name}}, upsert=True)
            await update.message.reply_text(f"Timezone set to {tz_name}")
        except ZoneInfoNotFoundError:
            await update.message.reply_text("Invalid timezone name. Use an IANA timezone like 'Europe/London'.")
        return

    # No args: prompt for location
    kb = [[KeyboardButton(text="Share location", request_location=True)]]
    await update.message.reply_text(
        "Please share your location so I can detect your timezone, or send /timezone <Region/City>.",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
    )
