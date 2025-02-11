# config.py - Store API keys
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot API Token
TELEGRAM_BOT_TOKEN = os.getenv("7202774752:AAF8rHHbAeFvhQRZIROXnX1lsFo6L-RBeiQ")

# Google Gemini AI API Key
GEMINI_API_KEY = os.getenv("AIzaSyCJnbD30bgcfmG_SkQ5G8eFciq-YgCBarY")

# Pexels API Key
PEXELS_API_KEY = os.getenv("uUl7VsSwswOyeLO9ay24Ij4SYIFSsnSDjix7RQEWzCGP9NQEn3dEwhsy")
