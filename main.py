import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from database.db import init_db
from agents.telegram_interface import setup_handlers

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    load_dotenv()
    
    # Initialize DB
    init_db()

    token = os.getenv("TG_BOT_TOKEN")
    if not token or token == "your_telegram_bot_token_here":
        logger.error("Please set TG_BOT_TOKEN in .env")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # on different commands - answer in Telegram
    setup_handlers(application)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
