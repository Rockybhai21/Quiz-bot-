import os
import logging
import asyncio
import json
import random
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot application
app = Application.builder().token(BOT_TOKEN).build()

# Dictionary to store quizzes and countdowns
quizzes = {}
countdowns = {}

# Load quizzes from file
def load_quizzes():
    global quizzes
    try:
        with open("quizzes.json", "r") as file:
            quizzes = json.load(file)
    except FileNotFoundError:
        quizzes = {}

# Save quizzes to file
def save_quizzes():
    with open("quizzes.json", "w") as file:
        json.dump(quizzes, file, indent=4)

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

# Handle quiz questions
async def handle_message(update: Update, context: CallbackContext) -> None:
    if context.user_data.get("quiz_step") == "adding_questions":
        lines = update.message.text.strip().split("\n")
        if len(lines) != 5:
            await update.message.reply_text("⚠️ Incorrect format! Send as:\n\nQuestion?\nOption1\nOption2\nOption3\nOption4\n✅ Correct Option")
            return

        question, *options, correct = lines
        correct = options.index(correct.replace("✅ ", "")) if "✅ " in correct else None
        if correct is None:
            await update.message.reply_text("⚠️ Mark the correct option with a ✅.")
            return

        context.user_data["quiz_questions"].append({
            "question": question,
            "options": options,
            "correct_answer": correct
        })
        count = len(context.user_data["quiz_questions"])
        await update.message.reply_text(f"✅ Question {count} saved! Send another or use /done to finish.")

# Finish quiz creation
async def done(update: Update, context: CallbackContext) -> None:
    if "quiz_questions" not in context.user_data or not context.user_data["quiz_questions"]:
        await update.message.reply_text("⚠️ No questions added. Use /create_quiz to start.")
        return

    quiz_id = generate_quiz_id()
    quizzes[quiz_id] = context.user_data["quiz_questions"]
    save_quizzes()

    keyboard = [[InlineKeyboardButton("▶️ Start Quiz", callback_data=f"start_quiz_{quiz_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"✅ Quiz saved with ID: {quiz_id}\nUse /start_quiz {quiz_id} to start.", reply_markup=reply_markup)
    context.user_data.clear()

# Countdown command with confirm/modify buttons
async def countdown(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        if not args or not args[0].isdigit():
            await update.message.reply_text("⚠️ Provide seconds. Example: /countdown 10")
            return

        seconds = int(args[0])
        chat_id = update.message.chat_id

        keyboard = [
            [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{chat_id}_{seconds}")],
            [InlineKeyboardButton("✏ Modify", callback_data="modify_countdown")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(f"⏳ Countdown: {seconds}s\nDo you want to start?", reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error in countdown: {e}")

# Handle countdown callbacks
async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    
    if data[0] == "confirm":
        chat_id = int(data[1])
        seconds = int(data[2])

        message = await query.message.edit_text(f"⏳ Countdown: {seconds}s remaining...")

        while seconds > 0:
            await asyncio.sleep(1)
            seconds -= 1
            await message.edit_text(f"⏳ Countdown: {seconds}s remaining...")

        await message.edit_text("🎉 TIME'S UP!")

    elif data[0] == "modify":
        await query.message.edit_text("✏ Modify countdown time with /countdown <seconds>")

# Start polling loop
async def main():
    load_quizzes()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create_quiz", create_quiz))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("countdown", countdown))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running in polling mode...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
