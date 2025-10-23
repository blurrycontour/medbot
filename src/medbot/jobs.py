import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .db import db
from .ai import get_dynamic_text


async def reminder_job(context):
    """Check and send reminders for users. Uses each user's timezone (IANA) so DST is respected."""
    for r in db.reminders.find({}):
        reminder_id = r.get('_id')
        user_id = r.get('user_id')

        # Validations
        reminder_time_str = r.get('time')
        if not reminder_time_str:
            continue
        try:
            reminder_time = datetime.strptime(reminder_time_str, "%H:%M").time()
        except ValueError:
            logging.error("Invalid reminder_time for reminder %s: %s", reminder_id, reminder_time_str)
            continue

        user = db.get_user(user_id)
        tz_name = user.get('tz') if user else None
        if not tz_name:
            logging.warning("No timezone set for user %s, skipping reminder %s", user_id, reminder_id)
            continue

        try:
            user_tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as e:
            logging.error("Invalid timezone for user %s: %s (%s)", user_id, tz_name, e)
            continue

        last_sent_str = r.get('last_sent_date')
        if last_sent_str:
            try:
                last_sent_date = datetime.strptime(last_sent_str, "%Y-%m-%d").date()
            except ValueError:
                logging.error("Invalid last_sent_date for reminder %s: %s", reminder_id, last_sent_str)
                last_sent_date = None
        else:
            last_sent_date = None

        # Sneding reminder logic
        now = datetime.now(user_tz)
        if last_sent_date != now.date() and now.time() >= reminder_time:
            try:
                logging.info("Sending reminder %s to user %s", reminder_id, user_id)
                pill_name = r.get('name', 'pills')
                first_name = user.get('first_name', 'user')
                reminder_text = get_dynamic_text(
                    f"Create a friendly medication reminder message for '{first_name}' to take their medicine named '{r.get('name')}' at {reminder_time_str}.",
                    default=f"It's time to take: {pill_name} 💊",
                    user_handle=user.get('username')
                )
                sent = await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️🚨👇 ({pill_name})\n\n{reminder_text}\n\nThen reply with a confirmation photo to this message for your reward 🏆"
                )
                db.reminders.update_one(
                    {'_id': reminder_id},
                    {'$set': {
                        'last_sent_date': now.date().isoformat(),
                        'confirmed': False,
                        'message_id': sent.message_id
                        }
                    }
                )
            except (ConnectionError, TimeoutError) as e:
                logging.error("Error sending reminder to %s: %s", user_id, e)
