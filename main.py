import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# ============ ЛОГІ ===================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ НАЛАШТУВАННЯ ============
TOKEN = os.getenv("BOT_TOKEN")  # зберігаємо токен в Render Environment
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook"

# ============ ТЕЛЕГРАМ БОТ ============
app_bot = Application.builder().token(TOKEN).build()

async def start(update: Update, context):
    await update.message.reply_text("Привіт 👋 Бот працює на Render!")

async def echo(update: Update, context):
    await update.message.reply_text(f"Ти написав: {update.message.text}")

# додаємо handlers
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ============ FLASK APP ===============
app = Flask(__name__)

@app.route("/")
def index():
    return "Бот працює 🚀"

@app.route("/webhook", methods=["POST"])
def webhook():
    """Отримує апдейти від Telegram"""
    try:
        update = Update.de_json(request.get_json(force=True), app_bot.bot)
        app_bot.update_queue.put_nowait(update)  # головне: передаємо апдейт у Application
    except Exception as e:
        logger.error(f"Помилка webhook: {e}")
    return "OK", 200

# ============ СТАРТ ==================
if __name__ == "__main__":
    import asyncio

    async def run():
        # встановлюємо webhook
        await app_bot.bot.set_webhook(WEBHOOK_URL)
        print(f"Webhook встановлено: {WEBHOOK_URL}")

    asyncio.run(run())

    # Запускаємо Flask (Render сам слухає PORT)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
