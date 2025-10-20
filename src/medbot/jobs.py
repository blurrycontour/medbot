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

        now = datetime.now(user_tz)

        last_sent_str = r.get('last_sent_date')
        if last_sent_str:
            try:
                last_sent = datetime.strptime(last_sent_str, "%Y-%m-%d").date()
            except ValueError:
                logging.error("Invalid last_sent_date for reminder %s: %s", reminder_id, last_sent_str)
                last_sent = None
        else:
            last_sent = None

        if not last_sent or not isinstance(last_sent, date):
            continue

        # If already sent today for this reminder, skip
        if confirmed and now.date() == last_sent:
            continue

        # If not sent today and confirmed is True
        confirmed = bool(r.get('confirmed'))
        if confirmed and now.date() != last_sent:
            confirmed = False
            db.reminders.update_one({'_id': reminder_id}, {'$set': {'confirmed': 0}})

        # Send normal reminder
        if not confirmed and last_sent != now.date() and now.time() >= reminder_time:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="📢📢📢\nIt's time to take your pills 💊!\nThen send a photo as confirmation."
                )
                # Mark this reminder as sent for today
                db.reminders.update_one({'_id': reminder_id}, {'$set': {'last_sent_date': now.date().isoformat()}})
            except (ConnectionError, TimeoutError) as e:
                logging.error("Error sending reminder to %s: %s", user_id, e)

        # Send follow-up if not confirmed by today
        repeated = r.get('repeated')
        new_reminder_time = reminder_time.replace(hour=reminder_time.hour + 1)
        if not confirmed and last_sent == now.date() and now.time() >= reminder_time:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="⏰ Reminder: Confirm you've taken your medication by sending a photo."
                )
            except (ConnectionError, TimeoutError) as e:
                logging.error("Error sending follow-up to %s: %s", user_id, e)
