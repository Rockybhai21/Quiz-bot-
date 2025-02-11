import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BARD_API_KEY = os.getenv("BARD_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
