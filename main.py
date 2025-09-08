import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== Логування =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== Telegram Bot =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
application = Application.builder().token(BOT_TOKEN).build()

# ===== Команда /temp =====
async def temp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Отримано апдейт: {update}")
    # Тут можна буде вставити реальний API погоди
    await update.message.reply_text("Температура у Львові зараз: 18°C 🌤️")

application.add_handler(CommandHandler("temp", temp))

# ===== Flask =====
flask_app = Flask(__name__)

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    """Отримує апдейти від Telegram"""
    data = request.get_json(force=True)
    logger.info(f"Webhook апдейт: {data}")
    update = Update.de_json(data, application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200

@flask_app.route("/")
def index():
    return "Bot is running!", 200

# ===== Точка входу для Gunicorn =====
app = flask_app
