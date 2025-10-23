import logging
from bson import ObjectId
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from timezonefinder import TimezoneFinder

from .ai import get_dynamic_text
from .db import db

# timezone finder instance (cheap to keep around)
tzfinder = TimezoneFinder()

logger = logging.getLogger(__name__)

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
        logger.warning("Could not determine timezone for location (%f, %f) from user %s", lat, lon, user_id)
        await update.message.reply_text(
            "Couldn't determine timezone from that location.\nPlease send /timezone <Region/City> instead.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    # Save tz (only update tz field)
    db.users.update_one({'user_id': user_id}, {'$set': {'tz': tz_name}}, upsert=True)
    logger.info("Set timezone for user %s to %s based on location (%f, %f)", user_id, tz_name, lat, lon)
    await update.message.reply_text(
        f"Detected timezone: {tz_name}",
        reply_markup=ReplyKeyboardRemove()
    )


async def handle_photo(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Handle a photo message as confirmation."""
    user_id = update.effective_user.id
    photo_msg_id = update.message.message_id
    reply = update.message.reply_to_message
    if reply:
        # check if this photo is a reply to a reminder message
        reply_msg_id = reply.message_id
        r = db.reminders.find_one({'user_id': user_id, 'message_id': reply_msg_id})
        if r: # reminder is followed up
            # if already confirmed
            already_confirmed = r.get('confirmed', False)
            if already_confirmed:
                await update.message.reply_text("Already confirmed. Well done 🎉🏆!")
                return
            # calculate streak
            nconfirmed = r.get('nconfirmed', 0) + 1
            streak = r.get('streak', 0)
            last_sent_date_str = r.get('last_sent_date')
            last_confirmed_date_str = r.get('last_confirmed_date')
            confirmed_date_str = last_sent_date_str
            if not last_confirmed_date_str:
                streak = 1  # first
                logger.info("First confirmation for reminder %s by user %s", r['_id'], user_id)
            else:
                last_confirmed_date = datetime.strptime(last_confirmed_date_str, "%Y-%m-%d").date()
                confirmed_date = datetime.strptime(confirmed_date_str, "%Y-%m-%d").date()
                if last_confirmed_date == (confirmed_date - timedelta(days=1)):
                    streak += 1
                    logger.info("Streak increased to %d for reminder %s by user %s", streak, r['_id'], user_id)
                else:
                    streak = 1  # reset streak
                    logger.info("Streak reset for reminder %s by user %s", r['_id'], user_id)
            db.reminders.update_one(
                {'_id': r['_id']},
                {'$set': {'confirmed': True, 'nconfirmed': nconfirmed, 'streak': streak, 'last_confirmed_date': confirmed_date_str}}
            )
            # give reward
            first_name = update.effective_user.first_name or "user"
            pill_name = r.get('name', 'pills')
            dynamic_reward_txt = get_dynamic_text(
                f"Generate a congratulatory and encouraging message for '{first_name}' who has followed up on their medication of {pill_name} today with streak of {streak} days.",
                default="✅ Good job! You're a nice person! 🎉🏆",
                user_handle=update.effective_user.username
            )
            await update.message.reply_text(
                f"{dynamic_reward_txt}\n\nCurrent streak: {streak} day{'s' if streak > 1 else ''} 🔥",
                reply_to_message_id=photo_msg_id
            )
            return

    await update.message.reply_text("Send confirmation photo as reply to the latest reminder message!")


async def handle_remove_callback(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks for removing reminders."""
    query = update.callback_query
    if not query:
        return
    await query.answer()  # acknowledge callback to Telegram

    data = query.data or ""
    user_id = query.from_user.id

    if data == "remove:cancel":
        await query.edit_message_text("Nothing removed!")
        return

    if data == "remove:all":
        res = db.reminders.delete_many({'user_id': user_id})
        await query.edit_message_text(f"Removed {res.deleted_count} reminders.")
        return

    if data.startswith("remove:"):
        rid = data.split(":", 1)[1]
        try:
            oid = ObjectId(rid)
        except Exception:
            logging.error("Invalid reminder id in remove callback: %s", rid)
            await query.edit_message_text("Invalid reminder id.")
            return

        deleted = db.reminders.find_one_and_delete({'_id': oid, 'user_id': user_id})
        if deleted:
            await query.edit_message_text(f"Removed reminder: {deleted.get('time')} - {deleted.get('name')}")
        else:
            await query.edit_message_text("No matching reminder found!")
        return
