# Use official Python image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (not necessary for Telegram bot, but good practice)
EXPOSE 8080

# Start bot
CMD ["python", "bot.py"]
