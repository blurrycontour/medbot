import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("APITOKEN")
ENV = os.getenv("ENV", "dev")

# Store user reminder times and confirmation status
user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to MedBot!\nUse /add <HH:MM> to set your daily medication reminder."
    )


async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /setreminder <HH:MM>")
        return
    try:
        reminder_time = datetime.strptime(context.args[0], "%H:%M").time()
        user_data[user_id] = {'reminder_time': reminder_time, 'confirmed': False}
        await update.message.reply_text(f"Reminder set for {reminder_time.strftime('%H:%M')}")
    except ValueError:
        await update.message.reply_text("Invalid time format. Use HH:MM.")


async def reminder_job(context):
    """Check and send reminders for users."""
    now = datetime.now().time()
    for user_id, data in user_data.items():
        if data['reminder_time'] and not data['confirmed'] and now >= data['reminder_time']:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="It's time to take your medication! Please send a photo as confirmation."
                )
                # Mark as reminded for today
                user_data[user_id]['confirmed'] = True
            except Exception as e:
                logging.error(f"Error sending reminder: {e}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data and user_data[user_id]['confirmed']:
        await update.message.reply_text("Thank you for confirming your medication intake!")
        # Reset confirmation for next day
        user_data[user_id]['confirmed'] = False
    else:
        await update.message.reply_text("No active reminder. Use /setreminder to set one.")


def main():
    """Start the bot."""
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("set", set_reminder))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Start reminder job - check every 30 seconds
    app.job_queue.run_repeating(reminder_job, interval=30, first=0)

    if ENV == "prod":
        webhook_url = os.getenv("WEBHOOK_URL", "https://your-domain.com/telegram-webhook")
        app.bot.set_webhook(url=webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=8443,
            webhook_url=webhook_url
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    # asyncio.run(main())
    main()
