import logging
from telegram import Update
from telegram.ext import ContextTypes
from timezonefinder import TimezoneFinder
from . import db

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
        await update.message.reply_text("Couldn't determine timezone from that location. Please send /settz <Region/City> instead.")
        return
    # Save tz (only update tz column)
    db.upsert_user(user_id, {'tz': tz_name})
    await update.message.reply_text(f"Detected timezone: {tz_name}")



async def handle_photo(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Try to find a reminder for today that was sent and not confirmed
    today = __import__("datetime").date.today()
    candidate = None
    for r in db.get_reminders_for_user(user_id):
        # r: id, user_id, time, confirmed, last_sent_date
        last_sent = r.get('last_sent_date')
        confirmed = bool(r.get('confirmed'))
        if last_sent == today.isoformat() and not confirmed:
            candidate = r
            break

    # fallback: most recent unconfirmed reminder
    if candidate is None:
        for r in db.get_reminders_for_user(user_id):
            if not bool(r.get('confirmed')):
                candidate = r
                break

    if candidate:
        db.set_confirmed(candidate['id'], True)
        await update.message.reply_text("Thank you for confirming your medication intake!")
    else:
        await update.message.reply_text("No active reminder. Use /setreminder to set one.")
