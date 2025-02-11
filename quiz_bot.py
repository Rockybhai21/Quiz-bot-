import requests
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import GEMINI_API_KEY, PEXELS_API_KEY, TELEGRAM_BOT_TOKEN

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app to keep the bot alive on Koyeb free plan
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

# Dictionary to store quizzes for users
user_quizzes = {}

# Function to generate quiz using Google Gemini AI
def generate_quiz(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response")
    return "Error generating quiz."

# Function to fetch an image from Pexels API
def get_image(query):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        photos = response.json().get("photos", [])
        return photos[0]["src"]["medium"] if photos else ""
    return ""

# Start command
def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("🎛 Settings", callback_data="settings")],
                [InlineKeyboardButton("❓ Help", callback_data="help")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Welcome to AI Quiz Maker Bot! Use /create_quiz to generate a quiz.", reply_markup=reply_markup)

# Create quiz command
def create_quiz(update: Update, context: CallbackContext):
    update.message.reply_text("Send a topic to generate a quiz. Example: 'Create 10 multiple-choice questions about space'")

# Handle quiz topic and generate quiz
def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    topic = update.message.text
    update.message.reply_text(f"Generating quiz for: {topic}...")
    
    quiz_text = generate_quiz(f"Create 10 multiple-choice questions about {topic}")
    questions = quiz_text.split('\n\n')
    
    user_quizzes[user_id] = []
    for q in questions:
        lines = q.split('\n')
        if len(lines) < 4:
            continue
        question = lines[0]
        options = lines[1:4]
        img_url = get_image(topic)
        options.append(f"🖼 Image: {img_url}" if img_url else "No image available.")
        user_quizzes[user_id].append({"question": question, "options": options})
    
    update.message.reply_text("Quiz created! Use /my_quizzes to view.")

# View saved quizzes
def my_quizzes(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    quizzes = user_quizzes.get(user_id, [])
    if not quizzes:
        update.message.reply_text("No quizzes found! Use /create_quiz to generate one.")
        return
    
    for i, quiz in enumerate(quizzes, 1):
        options = '\n'.join([f"{chr(65+j)}. {opt}" for j, opt in enumerate(quiz["options"])])
        update.message.reply_text(f"📌 Quiz {i}: {quiz['question']}\n\n{options}")

# Callback handler for inline buttons
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "settings":
        query.message.edit_text("Settings: Coming Soon!")
    elif query.data == "help":
        query.message.edit_text("This bot helps you create AI-generated quizzes. Use /create_quiz to start!")
    elif query.data == "close":
        query.message.delete()

# Run Flask server
def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Main function
def main():
    bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("create_quiz", create_quiz))
    bot_app.add_handler(CommandHandler("my_quizzes", my_quizzes))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    bot_app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is running...")
    threading.Thread(target=run_flask).start()  # Start Flask in a separate thread
    bot_app.run_polling(timeout=30, stop_signals=None)

if __name__ == "__main__":
    main()
