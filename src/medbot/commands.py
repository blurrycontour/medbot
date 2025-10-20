import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from .db import db

logger = logging.getLogger(__name__)


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hej! I'm MedBot!\n" \
        "I can send medication reminders at a time you choose.\n\n" \
        "I'll try to detect your timezone — send your location OR set it manually with\n/timezone <Region/City> (e.g. /timezone Europe/London)."
    )


async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    tz_name = user.get('tz')

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /set <HH:MM> <medicine-name>")
        return
    if not tz_name:
        await update.message.reply_text("Please set your timezone first using /timezone command.")
        return
    try:
        reminder_time = datetime.strptime(context.args[0], "%H:%M").time()
        name = context.args[1].strip()
        # add a reminder document for this user
        db.add_reminder({
            'user_id': user_id,
            'time': reminder_time.strftime("%H:%M"),
            'name': name,
            'confirmed': 0,
            'last_sent_date': None,
            'repeated': 0
        })
        await update.message.reply_text(f"Reminder set for {reminder_time.strftime('%H:%M')}")
    except ValueError:
        await update.message.reply_text("Invalid time format. Use HH:MM.")


async def settz(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await update.message.reply_text("Invalid timezone. Use an IANA timezone like 'Europe/London'.")
        return

    # No args: prompt for location
    kb = [[KeyboardButton(text="Share location", request_location=True)]]
    await update.message.reply_text(
        "Please share your location so I can detect your timezone, OR use /timezone <Region/City>.",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
    )


async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        reminders = list(db.get_reminders(user_id))
        if not reminders:
            await update.message.reply_text("No reminders set. Use /set to add one.")
            return
        msg_lines = ["Your reminders:"]
        for r in reminders:
            time_str = r.get('time')
            name = r.get('name')
            msg_lines.append(f"- Time: {time_str}, Name: {name}")
        await update.message.reply_text("\n".join(msg_lines))

    except ValueError:
        await update.message.reply_text("Error retrieving reminders.")


async def remove_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        reminders = list(db.get_reminders(user_id))
        if not reminders:
            await update.message.reply_text("No reminders set. Use /set to add one.")
            return
        # give user list of reminders as keyboard buttons to choose from
        kb = [[KeyboardButton(text=f"{r.get('time')} - {r.get('name')}")] for r in reminders]
        await update.message.reply_text(
            "Select a reminder to remove:",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
        )

    except ValueError:
        await update.message.reply_text("Error removing reminders.")
