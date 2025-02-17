FROM python:3.9

WORKDIR /app

COPY . /app
EXPOSE 8080
# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "bot.py"]
