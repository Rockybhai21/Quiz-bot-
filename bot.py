import os
import logging
import json
from telegram import Update, Poll
from telegram.ext import (
    Application, CommandHandler, CallbackContext, MessageHandler, filters
)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
QUIZ_STORAGE = "quizzes.json"  # File to store quizzes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to load quizzes
def load_quizzes():
    if os.path.exists(QUIZ_STORAGE):
        with open(QUIZ_STORAGE, "r") as file:
            return json.load(file)
    return []

# Function to save quizzes
def save_quizzes(quizzes):
    with open(QUIZ_STORAGE, "w") as file:
        json.dump(quizzes, file, indent=4)

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = "🎉 Welcome to the Quiz Bot!\n\nUse /create_quiz to create a quiz."
    await update.message.reply_text(welcome_message)

# Start creating a quiz
async def create_quiz(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("📋 Please send your quiz question:")
    context.user_data["quiz_step"] = "question"

# Handle quiz creation process
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text

    if "quiz_step" in context.user_data:
        step = context.user_data["quiz_step"]

        if step == "question":
            context.user_data["quiz_question"] = text
            context.user_data["quiz_options"] = []
            await update.message.reply_text("✅ Question saved! Now send up to **4 options** one by one.")
            context.user_data["quiz_step"] = "options"

        elif step == "options":
            if len(context.user_data["quiz_options"]) < 4:
                context.user_data["quiz_options"].append(text)

                if len(context.user_data["quiz_options"]) == 4:
                    await update.message.reply_text(
                        "🎯 Now send the correct option number (1, 2, 3, or 4)."
                    )
                    context.user_data["quiz_step"] = "correct_answer"
                else:
                    await update.message.reply_text(f"✅ Option {len(context.user_data['quiz_options'])} saved! Send another option.")

        elif step == "correct_answer":
            if text.isdigit() and 1 <= int(text) <= 4:
                context.user_data["quiz_correct"] = int(text) - 1
                await update.message.reply_text("✅ Quiz data saved! Use /done to finalize and save the quiz.")

                context.user_data["quiz_step"] = "done"
            else:
                await update.message.reply_text("⚠️ Please send a valid number (1-4).")

# Finalize quiz creation
async def done(update: Update, context: CallbackContext) -> None:
    if "quiz_question" in context.user_data and "quiz_options" in context.user_data:
        quiz = {
            "question": context.user_data["quiz_question"],
            "options": context.user_data["quiz_options"],
            "correct": context.user_data["quiz_correct"]
        }

        quizzes = load_quizzes()
        quizzes.append(quiz)
        save_quizzes(quizzes)

        await update.message.reply_text("🎉 Quiz saved! Use /start_quiz to start a saved quiz.")
        context.user_data.clear()
    else:
        await update.message.reply_text("⚠️ No quiz in progress. Use /create_quiz to start one.")

# List saved quizzes
async def start_quiz(update: Update, context: CallbackContext) -> None:
    quizzes = load_quizzes()

    if not quizzes:
        await update.message.reply_text("⚠️ No saved quizzes. Use /create_quiz to create one.")
        return

    for i, quiz in enumerate(quizzes):
        await update.message.reply_poll(
            question=quiz["question"],
            options=quiz["options"],
            type=Poll.QUIZ,
            correct_option_id=quiz["correct"],
            is_anonymous=False
        )

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create_quiz", create_quiz))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("start_quiz", start_quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    app.run_polling()

if __name__ == "__main__":
    main()
