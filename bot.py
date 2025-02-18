import os
import logging
import json
import random
import string
from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Set your webhook URL
PORT = int(os.getenv("PORT", 8080))  # Default port for Koyeb

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Telegram Bot
tg_app = Application.builder().token(BOT_TOKEN).build()

# Dictionary to store quizzes
saved_quizzes = {}

# Load quizzes from JSON file
def load_quizzes_from_file():
    global saved_quizzes
    try:
        with open("quizzes.json", "r") as file:
            saved_quizzes = json.load(file)
    except FileNotFoundError:
        saved_quizzes = {}

# Save quizzes to JSON file
def save_quizzes_to_file():
    with open("quizzes.json", "w") as file:
        json.dump(saved_quizzes, file, indent=4)

# Generate a unique quiz ID
def generate_quiz_id():
    return "quiz_" + "".join(random.choices(string.ascii_letters + string.digits, k=6))

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🎉 Welcome to the Quiz Bot! Use /create_quiz to create a quiz.")

# Create quiz command
async def create_quiz(update: Update, context: CallbackContext) -> None:
    context.user_data["quiz_questions"] = []
    await update.message.reply_text("📋 Send your quiz questions in the format:\n\nQuestion?\nOption1\nOption2\nOption3\nOption4\n✅ Correct Option")
    context.user_data["quiz_step"] = "adding_questions"

# Handle messages for quiz questions
async def handle_message(update: Update, context: CallbackContext) -> None:
    if context.user_data.get("quiz_step") == "adding_questions":
        lines = update.message.text.strip().split("\n")
        if len(lines) != 5:
            await update.message.reply_text("⚠️ Incorrect format! Please send in this format:\n\nQuestion?\nOption1\nOption2\nOption3\nOption4\n✅ Correct Option")
            return
        
        question, *options, correct = lines
        correct = options.index(correct.replace("✅ ", "")) if "✅ " in correct else None
        if correct is None:
            await update.message.reply_text("⚠️ You must mark the correct option with a ✅.")
            return

        context.user_data["quiz_questions"].append({
            "question": question,
            "options": options,
            "correct_answer": correct
        })
        count = len(context.user_data["quiz_questions"])
        await update.message.reply_text(f"✅ Question {count} saved! Send another or use /done to finish.")

# Finalize quiz creation
async def done(update: Update, context: CallbackContext) -> None:
    if "quiz_questions" not in context.user_data or not context.user_data["quiz_questions"]:
        await update.message.reply_text("⚠️ No questions added. Use /create_quiz to start.")
        return
    
    quiz_id = generate_quiz_id()
    saved_quizzes[quiz_id] = context.user_data["quiz_questions"]
    save_quizzes_to_file()
    
    keyboard = [[InlineKeyboardButton("▶️ Start Quiz", callback_data=f"start_quiz_{quiz_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(f"✅ Quiz saved with ID: {quiz_id}\nUse /start_quiz {quiz_id} to start it anytime.", reply_markup=reply_markup)
    context.user_data.clear()

# Set Webhook
async def set_webhook():
    await tg_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

@app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), tg_app.bot)
    await tg_app.process_update(update)
    return "OK"

# Main function
async def main():
    load_quizzes_from_file()
    await set_webhook()

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("create_quiz", create_quiz))
    tg_app.add_handler(CommandHandler("done", done))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
