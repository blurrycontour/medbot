from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from timezonefinder import TimezoneFinder
from datetime import date

from .db import db

# timezone finder instance (cheap to keep around)
tzfinder = TimezoneFinder()


async def handle_location(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Handle a location message and map it to an IANA timezone."""
    user_id = update.effective_user.id
    loc = update.message.location
    if not loc:
        await update.message.reply_text("No location found in the message.")
        return
    lat, lon = loc.latitude, loc.longitude
    tz_name = tzfinder.timezone_at(lat=lat, lng=lon)

    if not tz_name:
        await update.message.reply_text(
            "Couldn't determine timezone from that location.\nPlease send /timezone <Region/City> instead.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    # Save tz (only update tz field)
    db.users.update_one({'user_id': user_id}, {'$set': {'tz': tz_name}}, upsert=True)
    await update.message.reply_text(
        f"Detected timezone: {tz_name}",
        reply_markup=ReplyKeyboardRemove()
    )


async def handle_photo(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Try to find a reminder for today that was sent and not confirmed
    today = date.today()
    candidate = None
    # find reminders for user
    for r in db.reminders.find({'user_id': user_id}).sort([('last_sent_date', -1), ('_id', -1)]):
        # r: id, user_id, time, confirmed, last_sent_date
        last_sent = r.get('last_sent_date')
        confirmed = bool(r.get('confirmed'))
        if last_sent == today.isoformat() and not confirmed:
            candidate = r
            break

    # fallback: most recent unconfirmed reminder
    if candidate is None:
        for r in db.reminders.find({'user_id': user_id, 'confirmed': {'$in': [0, False]}}).sort([('_id', -1)]):
            candidate = r
            break

    if candidate:
        # mark this reminder as confirmed
        db.reminders.update_one({'_id': candidate['_id']}, {'$set': {'confirmed': 1}})
        await update.message.reply_text("Thank you for confirming your medication intake!")
    else:
        await update.message.reply_text("No active reminder. Use /setreminder to set one.")
