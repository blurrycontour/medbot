"""
Run this in botfather to set commands
/setcommands
start - Get started
timezone - Set your timezone
set - Create a new reminder
list - List all your reminders
stats - Your statistics
remove - Remove a reminder or all reminders
help - Help
"""
import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from . import utils
utils.setup_logging(log_level=logging.INFO)
from . import jobs, handlers, commands

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENV = os.getenv("ENVIRONMENT")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

def run():
    """Setup and create the bot application."""
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", commands.start))
    app.add_handler(CommandHandler("timezone", commands.settz))
    app.add_handler(CommandHandler("set", commands.set_reminder))
    app.add_handler(CommandHandler("list", commands.list_reminders))
    app.add_handler(CommandHandler("remove", commands.remove_reminder))
    app.add_handler(CommandHandler("stats", commands.user_stats))
    app.add_handler(CommandHandler("help", commands.help_command))
    if ADMIN_USER_ID:
        app.add_handler(CommandHandler("debug", commands.debug, filters=filters.User(int(ADMIN_USER_ID))))
    app.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
    app.add_handler(MessageHandler(filters.LOCATION, handlers.handle_location))
    app.add_handler(CallbackQueryHandler(handlers.handle_remove_callback, pattern="^remove:"))

    # Start reminder job - check every 30 seconds
    app.job_queue.run_repeating(jobs.reminder_job, interval=30, first=0)

    if ENV == "prod":
        webhook_url = os.getenv("WEBHOOK_URL")
        app.bot.set_webhook(url=webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=8443,
            webhook_url=webhook_url
        )
    else:
        app.run_polling()


if __name__ == "__main__":
    run()
