import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .db import db




async def reminder_job(context):
    """Check and send reminders for users. Uses each user's timezone (IANA) so DST is respected."""
    for r in db.reminders.find({}):
        reminder_id = r.get('_id')
        user_id = r.get('user_id')
        reminder_time_str = r.get('time')
        if not reminder_time_str:
            continue
        try:
            reminder_time = datetime.strptime(reminder_time_str, "%H:%M").time()
        except ValueError:
            logging.error("Invalid reminder_time for reminder %s: %s", reminder_id, reminder_time_str)
            continue

        user = db.users.find_one({'user_id': user_id})
        tz_name = user.get('tz') if user else None
        if not tz_name:
            continue

        try:
            user_tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as e:
            logging.error("Invalid timezone for user %s: %s (%s)", user_id, tz_name, e)
            continue

        now = datetime.now(user_tz)

        last_sent_str = r.get('last_sent_date')
        if last_sent_str:
            try:
                last_sent = datetime.strptime(last_sent_str, "%Y-%m-%d").date()
            except ValueError:
                last_sent = None
        else:
            last_sent = None

        # If already sent today for this reminder, skip
        if isinstance(last_sent, date) and last_sent == now.date():
            continue

        confirmed = bool(r.get('confirmed'))
        if not confirmed and now.time() >= reminder_time:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="📢📢📢\nTake your pills 💊 now!\nThen send a photo as confirmation."
                )
                # Mark this reminder as sent for today
                db.reminders.update_one({'_id': reminder_id}, {'$set': {'confirmed': 1, 'last_sent_date': now.date().isoformat()}})
            except (ConnectionError, TimeoutError) as e:
                logging.error("Error sending reminder to %s: %s", user_id, e)
