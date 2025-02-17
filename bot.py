import os
import logging
import random
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Sample quiz questions
QUESTIONS = [
    {
        "question": "What is the capital of France?",
        "options": ["Berlin", "Paris", "Madrid", "Rome"],
        "answer": 1  # Index of the correct answer
    },
    {
        "question": "What is 5 + 7?",
        "options": ["10", "11", "12", "13"],
        "answer": 2
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "options": ["Earth", "Mars", "Venus", "Jupiter"],
        "answer": 1
    }
]

# Function to start the quiz
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Welcome to the Quiz Bot! Type /quiz to start the quiz.")

# Function to send a random quiz question
async def quiz(update: Update, context: CallbackContext) -> None:
    question = random.choice(QUESTIONS)
    context.user_data["current_question"] = question

    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(i)) for i, option in enumerate(question["options"])]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(question["question"], reply_markup=reply_markup)

# Function to handle answer selection
async def answer(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    selected_option = int(query.data)
    question = context.user_data.get("current_question")

    if question and selected_option == question["answer"]:
        response = "✅ Correct!"
    else:
        response = f"❌ Wrong! The correct answer was: {question['options'][question['answer']]}"

    await query.edit_message_text(text=response)

# Main function to run the bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(answer))

    logging.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
