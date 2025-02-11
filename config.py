# config.py - Store API keys
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot API Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Google Gemini AI API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Pexels API Key
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
