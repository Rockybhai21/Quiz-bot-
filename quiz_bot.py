import logging
import requests
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from config import TELEGRAM_BOT_TOKEN, BARD_API_KEY, PEXELS_API_KEY

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Store quizzes
user_quizzes = {}

# Google Bard API Request
def generate_quiz(prompt):
    url = f"https://api.bard.google.com/v1/quiz?api_key={BARD_API_KEY}"
    response = requests.post(url, json={"prompt": prompt})
    return response.json()["questions"]

# Pexels API Request for Images
def get_image(query):
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    headers = {"Authorization": PEXELS_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()["photos"][0]["src"]["medium"]

# Start Command
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🎛 Settings", callback_data="settings"),
         InlineKeyboardButton("🤔 Help", callback_data="help")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "Hello! I'm a Quiz Bot.\n\n"
        "I can create AI-generated quizzes for you.\n\n"
        "/create_quiz - Generate a quiz\n"
        "/my_quizzes - Show your saved quizzes",
        reply_markup=reply_markup
    )

# Quiz Creation
def create_quiz(update: Update, context: CallbackContext):
    update.message.reply_text("Send a topic for your quiz (e.g., 'Computer Basics').")
    return "WAITING_FOR_TOPIC"

# Handle Quiz Topic
def handle_topic(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    topic = update.message.text
    update.message.reply_text(f"Generating questions for: {topic}...")

    # Generate questions
    questions = generate_quiz(f"Create 10 multiple-choice questions about {topic}")

    # Add image for the 4th option
    for question in questions:
        question["options"][3] = get_image(topic)

    user_quizzes[user_id] = questions
    update.message.reply_text("Quiz created! Use /my_quizzes to see your quizzes.")

# Show User Quizzes
def my_quizzes(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    quizzes = user_quizzes.get(user_id, [])
    
    if not quizzes:
        update.message.reply_text("No quizzes found! Create one using /create_quiz.")
        return
    
    for i, quiz in enumerate(quizzes, 1):
        options = "\n".join([f"{chr(65+j)}. {opt}" for j, opt in enumerate(quiz["options"])])
        update.message.reply_photo(
            quiz["options"][3] if quiz["options"][3].startswith("http") else None,
            caption=f"📌 **Quiz {i}:** {quiz['question']}\n\n{options}",
            parse_mode="Markdown"
        )

# Settings Menu
def settings(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📝 Language: en", callback_data="set_lang"),
         InlineKeyboardButton("🔀 Shuffle: On", callback_data="set_shuffle")],
        [InlineKeyboardButton("⏳ Time Limit: 45 sec", callback_data="set_time"),
         InlineKeyboardButton("✂ Negative Marking: No", callback_data="set_negative")],
        [InlineKeyboardButton("⚙ Reset Settings", callback_data="reset"),
         InlineKeyboardButton("❌ Close Settings", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.callback_query.message.edit_text("⚙ Config Bot Settings", reply_markup=reply_markup)

# Callback Handler
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "settings":
        settings(update, context)
    elif query.data == "help":
        query.message.edit_text("This bot helps you create AI-generated quizzes.\nUse /create_quiz to start!")
    elif query.data == "close":
        query.message.delete()

# Main Function
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("create_quiz", create_quiz))
    dp.add_handler(CommandHandler("my_quizzes", my_quizzes))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_topic))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
