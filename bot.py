import os
import logging
import json
import random
import string
from flask import Flask, request
from telegram import Update, Poll, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackContext, MessageHandler,
    filters, CallbackQueryHandler
)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://yourdomain.com
PORT = int(os.getenv("PORT", 8443))  # Default port

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App for handling webhooks
app = Flask(__name__)

# Dictionary to store quizzes
saved_quizzes = {}
user_quiz_sessions = {}

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

# Start saved quiz
async def start_saved_quiz(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Please provide a quiz ID. Example: /start_quiz quiz_ABC123")
        return
    
    quiz_id = context.args[0]
    if quiz_id not in saved_quizzes:
        await update.message.reply_text("⚠️ Quiz not found!")
        return
    
    context.user_data["current_quiz"] = quiz_id
    context.user_data["question_index"] = 0
    await send_next_question(update, context)

async def send_next_question(update: Update, context: CallbackContext):
    quiz_id = context.user_data["current_quiz"]
    index = context.user_data["question_index"]
    quiz = saved_quizzes[quiz_id]

    if index >= len(quiz):
        await update.message.reply_text("🎉 Quiz completed!")
        return
    
    question_data = quiz[index]
    await update.message.reply_poll(
        question=question_data["question"],
        options=question_data["options"],
        type=Poll.QUIZ,
        correct_option_id=question_data["correct_answer"],
        is_anonymous=False
    )
    
    context.user_data["question_index"] += 1

# Callback for quiz start buttons
async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if query.data.startswith("start_quiz_"):
        quiz_id = query.data.replace("start_quiz_", "")
        context.user_data["current_quiz"] = quiz_id
        context.user_data["question_index"] = 0
        await send_next_question(query.message, context)

# Telegram Bot Initialization
telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("create_quiz", create_quiz))
telegram_app.add_handler(CommandHandler("done", done))
telegram_app.add_handler(CommandHandler("start_quiz", start_saved_quiz))
telegram_app.add_handler(CallbackQueryHandler(button_callback))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask Webhook Endpoint
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Process incoming webhook updates from Telegram."""
    update = Update.de_json(request.get_json(), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "OK", 200

# Set Webhook in Telegram
def set_webhook():
    """Register webhook with Telegram."""
    webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
    response = telegram_app.bot.set_webhook(url=webhook_url)
    if response:
        logger.info(f"Webhook set successfully: {webhook_url}")
    else:
        logger.error(f"Failed to set webhook: {webhook_url}")

# Start Flask Server & Register Webhook
if __name__ == "__main__":
    load_quizzes_from_file()
    set_webhook()
    app.run(host="0.0.0.0", port=PORT)
