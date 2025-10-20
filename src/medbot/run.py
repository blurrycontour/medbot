import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from . import jobs, handlers, commands, utils

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENV = os.getenv("ENVIRONMENT")


def run():
    """Setup and create the bot application."""
    utils.setup_logging(log_level=logging.INFO)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], commands.start))
    app.add_handler(CommandHandler("set", commands.set_reminder))
    app.add_handler(CommandHandler("list", commands.list_reminders))
    app.add_handler(CommandHandler("remove", commands.remove_reminder))
    app.add_handler(CommandHandler("timezone", commands.settz))
    app.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
    app.add_handler(MessageHandler(filters.LOCATION, handlers.handle_location))

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
