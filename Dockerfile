# Use official Python image as a base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code into the container
COPY . .

# Expose the Flask port (default 8443)
EXPOSE 8443

# Command to run the application
CMD ["python", "bot.py"]
