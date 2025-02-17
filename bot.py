import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Flask app for webhook handling
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Quiz Bot is Running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot)
    application.update_queue.put(update)
    return "OK", 200

# Telegram bot setup
bot = Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

logging.basicConfig(level=logging.INFO)

# Command Handlers
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to the Quiz Bot! Use /quiz to start.")

def quiz(update: Update, context: CallbackContext):
    question = "What is the capital of France?\nA) Madrid\nB) Berlin\nC) Paris\nD) Rome"
    context.user_data["answer"] = "C"
    update.message.reply_text(question)

def answer(update: Update, context: CallbackContext):
    user_answer = update.message.text.strip().upper()
    correct_answer = context.user_data.get("answer")
    if user_answer == correct_answer:
        update.message.reply_text("✅ Correct!")
    else:
        update.message.reply_text("❌ Wrong! Try again.")

# Adding handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("quiz", quiz))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer))

if __name__ == "__main__":
    # Set webhook
    bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")
    logging.info("Bot started with webhook!")
    app.run(host="0.0.0.0", port=8080)
