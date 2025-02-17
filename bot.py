import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters

# Load bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define the /start command
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = "🎉 Welcome to the Quiz Bot! Use /crea_quiz to create a quiz."
    await update.message.reply_text(welcome_message)

# Define the /crea_quiz command
async def crea_quiz(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Start Quiz", callback_data="start_quiz")],
        [InlineKeyboardButton("Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("📋 Ready to create a quiz?", reply_markup=reply_markup)

# Handle button clicks
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "start_quiz":
        await query.message.reply_text("🚀 Let's start your quiz! Send me a question.")
    elif query.data == "help":
        await query.message.reply_text("ℹ️ Use /crea_quiz to start quiz creation.")

# Main function to start the bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crea_quiz", crea_quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, crea_quiz))
    
    app.run_polling()

if __name__ == "__main__":
    main()
