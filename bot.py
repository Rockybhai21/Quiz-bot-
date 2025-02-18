import os
import logging
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store saved quizzes
saved_quizzes = {}

# Dummy HTTP server for health checks
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_http_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthCheckHandler)
    server.serve_forever()

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

# Help command
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = """
📚 **Quiz Bot Commands**:
- /start - Start the bot.
- /create_quiz - Create a new quiz.
- /done - Save the quiz.
- /start_quiz <quiz_id> - Start a saved quiz.
- /list_quizzes - List all saved quizzes.
- /help - Show this help message.
    """
    await update.message.reply_text(help_text)

# Create quiz command
async def create_quiz(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("📋 Please send your quiz question:")
    context.user_data["quiz_step"] = "question"
    context.user_data["quiz_category"] = None  # Initialize category

# Handle messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text

    if "quiz_step" in context.user_data:
        step = context.user_data["quiz_step"]

        if step == "question":
            context.user_data["quiz_question"] = text
            context.user_data["quiz_options"] = []
            await update.message.reply_text("✅ Question saved! Now send the category for this quiz:")
            context.user_data["quiz_step"] = "category"

        elif step == "category":
            context.user_data["quiz_category"] = text
            await update.message.reply_text("✅ Category saved! Now send up to 4 options one by one.")
            context.user_data["quiz_step"] = "options"

        elif step == "options":
            if len(context.user_data["quiz_options"]) < 4:
                context.user_data["quiz_options"].append(text)

                if len(context.user_data["quiz_options"]) == 4:
                    await update.message.reply_text("🎯 Now send the correct option number (1, 2, 3, or 4).")
                    context.user_data["quiz_step"] = "correct_answer"
                else:
                    await update.message.reply_text(f"✅ Option {len(context.user_data['quiz_options'])} saved! Send another option.")

        elif step == "correct_answer":
            if text.isdigit() and 1 <= int(text) <= 4:
                context.user_data["quiz_correct"] = int(text) - 1
                await update.message.reply_text("🎉 Quiz saved! Use /done to finalize or send more options.")
                context.user_data["quiz_step"] = "done"
            else:
                await update.message.reply_text("⚠️ Please send a valid number (1-4).")

# Command to finalize quiz creation
async def done(update: Update, context: CallbackContext) -> None:
    if "quiz_question" in context.user_data:
        quiz_id = f"quiz_{len(saved_quizzes) + 1}"
        saved_quizzes[quiz_id] = {
            "question": context.user_data["quiz_question"],
            "options": context.user_data["quiz_options"],
            "correct_answer": context.user_data["quiz_correct"],
            "category": context.user_data["quiz_category"]  # Add category
        }
        save_quizzes_to_file()  # Save quizzes to file
        await update.message.reply_text(f"✅ Quiz saved with ID: {quiz_id}. Use /start_quiz {quiz_id} to start it.")
        context.user_data.clear()
    else:
        await update.message.reply_text("⚠️ No quiz to save. Use /create_quiz to start creating a quiz.")

# Command to start a saved quiz
async def start_saved_quiz(update: Update, context: CallbackContext) -> None:
    if len(context.args) == 1:
        quiz_id = context.args[0]
        if quiz_id in saved_quizzes:
            quiz = saved_quizzes[quiz_id]

            # Send the poll
            if update.message:
                await update.message.reply_poll(
                    question=quiz["question"],
                    options=quiz["options"],
                    type=Poll.QUIZ,
                    correct_option_id=quiz["correct_answer"],
                    is_anonymous=False
                )
            else:
                await context.bot.send_poll(
                    chat_id=update.effective_chat.id,
                    question=quiz["question"],
                    options=quiz["options"],
                    type=Poll.QUIZ,
                    correct_option_id=quiz["correct_answer"],
                    is_anonymous=False
                )
        else:
            await update.message.reply_text("⚠️ Quiz not found.")
    else:
        await update.message.reply_text("⚠️ Please provide a quiz ID. Use /list_quizzes to see available quizzes.")

# Command to list saved quizzes
async def list_quizzes(update: Update, context: CallbackContext) -> None:
    if saved_quizzes:
        quizzes_list = "\n".join([f"{quiz_id}: {saved_quizzes[quiz_id]['question']} (Category: {saved_quizzes[quiz_id]['category']})" for quiz_id in saved_quizzes])
        await update.message.reply_text(f"📚 Saved Quizzes:\n{quizzes_list}")
    else:
        await update.message.reply_text("📚 No quizzes saved yet.")

# Main function
def main():
    # Load quizzes from file
    load_quizzes_from_file()

    # Start the HTTP server for health checks
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # Create the Application
    app = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("create_quiz", create_quiz))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("start_quiz", start_saved_quiz))
    app.add_handler(CommandHandler("list_quizzes", list_quizzes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    logger.info("Starting bot in polling mode...")
    app.run_polling()

if __name__ == "__main__":
    main()
