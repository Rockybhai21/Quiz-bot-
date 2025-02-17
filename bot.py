import os
import logging
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: https://your-domain.com/webhook

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = "🎉 Welcome to the Quiz Bot!\n\nUse /create_quiz to create a quiz."
    await update.message.reply_text(welcome_message)

# Step 1: Ask the question
async def create_quiz(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("📋 Please send your quiz question:")
    context.user_data["quiz_step"] = "question"

# Step 2: Store question and ask for options
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
                await update.message.reply_text("🎉 Quiz saved! Sending now...")
                
                # Send the poll (quiz)
                await update.message.chat.send_poll(
                    question=context.user_data["quiz_question"],
                    options=context.user_data["quiz_options"],
                    type=Poll.QUIZ,
                    correct_option_id=context.user_data["quiz_correct"],
                    is_anonymous=False
                )

                # Clear quiz data
                context.user_data.clear()
            else:
                await update.message.reply_text("⚠️ Please send a valid number (1-4).")

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("create_quiz", create_quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Use webhook on port 8080
    app.run_webhook(
        listen="0.0.0.0",
        port=8080,
        url_path=BOT_TOKEN,  # Security: Use token as path
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"  # Full webhook URL
    )

if __name__ == "__main__":
    main()
