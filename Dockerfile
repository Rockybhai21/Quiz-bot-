# Use Python base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (for health checks)
EXPOSE 8080

# Run the bot
CMD ["python", "quiz_bot.py"]
