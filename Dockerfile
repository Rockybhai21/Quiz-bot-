# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot files
COPY . .

# Expose the Flask port
EXPOSE 8443

# Run the bot using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8443", "bot:app"]
