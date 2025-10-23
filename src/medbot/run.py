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
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

from . import utils
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
utils.setup_logging(log_level=LOG_LEVEL, file_logger_names=["httpx"])
from . import jobs, handlers, commands, debug

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
        app.add_handler(CommandHandler("info", debug.info, filters=filters.User(int(ADMIN_USER_ID))))
        app.add_handler(CommandHandler("users", debug.user_list, filters=filters.User(int(ADMIN_USER_ID))))
        app.add_handler(CommandHandler("sudolist", debug.sudo_list_reminders, filters=filters.User(int(ADMIN_USER_ID))))
    app.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
    app.add_handler(MessageHandler(filters.LOCATION, handlers.handle_location))
    app.add_handler(CallbackQueryHandler(handlers.handle_remove_callback, pattern="^remove:"))
    app.add_handler(CallbackQueryHandler(handlers.handle_sudolist_callback, pattern="^sudolist:"))

    # Start reminder job - check every 30 seconds
    app.job_queue.run_repeating(jobs.reminder_job, interval=30, first=0)

    app.run_polling()


if __name__ == "__main__":
    run()
