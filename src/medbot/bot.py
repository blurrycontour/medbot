import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import os
from dotenv import load_dotenv

from . import db, jobs, handlers, commands, utils

# Load environment variables
load_dotenv()
TOKEN = os.getenv("APITOKEN")
ENV = os.getenv("ENVIRONMENT")


def main():
    """Setup and create the bot application."""
    utils.setup_logging(log_level=logging.DEBUG, log_file="bot.log")
    db.init_db()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler(["start", "help"], commands.start))
    app.add_handler(CommandHandler("setreminder", commands.set_reminder))
    app.add_handler(CommandHandler("settz", commands.settz))
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
    main()
