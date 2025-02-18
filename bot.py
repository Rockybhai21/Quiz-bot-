import os
import logging
import json
import threading
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store saved quizzes
saved_quizzes = {}

# Save quizzes to JSON file
def save_quizzes_to_file():
    with open("quizzes.json", "w") as file:
        json.dump(saved_quizzes, file)

# Load quizzes from JSON file
def load_quizzes_from_file():
    global saved_quizzes
    try:
        with open("quizzes.json", "r") as file:
            saved_quizzes = json.load(file)
    except FileNotFoundError:
        saved_quizzes = {}

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🎉 Welcome to the Quiz Bot! Use /create_quiz to create a quiz.")

# Create quiz command
async def create_quiz(update: Update, context: CallbackContext) -> None:
    context.user_data["quiz_questions"] = []
    await update.message.reply_text("📋 Send your quiz questions in this format:\n\nWhat is the capital of India?\nNew Delhi ✅\nKolkata\nMadurai\nChennai\n\nWhen done, type /done.")

# Handle messages for quiz creation
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    lines = text.split("\n")
    
    if len(lines) >= 2:
        question = lines[0]
        options = [line.replace(" ✅", "") for line in lines[1:]]
        correct_option = next((i for i, line in enumerate(lines[1:]) if "✅" in line), None)
        
        if correct_option is not None:
            context.user_data["quiz_questions"].append({
                "question": question,
                "options": options,
                "correct_option": correct_option
            })
            await update.message.reply_text(f"✅ Question added! Total: {len(context.user_data['quiz_questions'])} questions. Send another or type /done.")
        else:
            await update.message.reply_text("⚠️ Please mark the correct answer with a ✅.")
    else:
        await update.message.reply_text("⚠️ Invalid format. Please send the question in the correct format.")

# Command to finalize quiz creation
async def done(update: Update, context: CallbackContext) -> None:
    if "quiz_questions" in context.user_data and context.user_data["quiz_questions"]:
        quiz_id = f"quiz_{len(saved_quizzes) + 1}"
        saved_quizzes[quiz_id] = context.user_data["quiz_questions"]
        save_quizzes_to_file()
        
        await update.message.reply_text(f"✅ Quiz saved with ID: {quiz_id}. Use /start_quiz {quiz_id} to start it.")
        context.user_data.clear()
    else:
        await update.message.reply_text("⚠️ No questions added. Use /create_quiz to start.")

# Command to start a saved quiz
async def start_saved_quiz(update: Update, context: CallbackContext) -> None:
    if len(context.args) == 1:
        quiz_id = context.args[0]
        if quiz_id in saved_quizzes:
            for question_data in saved_quizzes[quiz_id]:
                await update.message.reply_poll(
                    question=question_data["question"],
                    options=question_data["options"],
                    type=Poll.QUIZ,
                    correct_option_id=question_data["correct_option"],
                    is_anonymous=False
                )
        else:
            await update.message.reply_text("⚠️ Quiz not found.")
    else:
        await update.message.reply_text("⚠️ Please provide a quiz ID. Use /list_quizzes to see available quizzes.")

# Command to list saved quizzes
async def list_quizzes(update: Update, context: CallbackContext) -> None:
    if saved_quizzes:
        quizzes_list = "\n".join([f"{quiz_id}: {len(saved_quizzes[quiz_id])} questions" for quiz_id in saved_quizzes])
        await update.message.reply_text(f"📚 Saved Quizzes:\n{quizzes_list}")
    else:
        await update.message.reply_text("📚 No quizzes saved yet.")

# Main function
def main():
    load_quizzes_from_file()
    
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create_quiz", create_quiz))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("start_quiz", start_saved_quiz))
    app.add_handler(CommandHandler("list_quizzes", list_quizzes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Starting bot in polling mode...")
    app.run_polling()

if __name__ == "__main__":
    main()

