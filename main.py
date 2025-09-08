import os
import requests
from flask import Flask, request
import telebot
from telebot import types

# =======================
# Налаштування
# =======================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # зберігай токен у Render Environment
WEBHOOK_URL = "https://exchangeforme.onrender.com/webhook"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# =======================
# Джерела даних
# =======================

def get_exchange_rates():
    """Отримати курси валют з НБУ"""
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    try:
        data = requests.get(url, timeout=5).json()
        usd = next(item for item in data if item["cc"] == "USD")["rate"]
        eur = next(item for item in data if item["cc"] == "EUR")["rate"]
        pln = next(item for item in data if item["cc"] == "PLN")["rate"]
        return f"💵 USD: {usd:.2f}₴\n💶 EUR: {eur:.2f}₴\n🇵🇱 PLN: {pln:.2f}₴"
    except Exception:
        return "⚠️ Не вдалося завантажити курси валют."

def get_crypto():
    """Отримати топ-10 криптовалют з CoinGecko"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
    try:
        data = requests.get(url, params=params, timeout=5).json()
        result = "₿ Топ-10 криптовалют:\n"
        for coin in data:
            result += f"{coin['symbol'].upper()}: {coin['current_price']}$\n"
        return result
    except Exception:
        return "⚠️ Не вдалося завантажити криптовалюти."

def get_fuel_prices():
    """Отримати ціни на пальне з OKKO"""
    url = "https://api.okko.ua/fuel/prices"
    try:
        data = requests.get(url, timeout=5).json()
        prices = data.get("data", [])
        result = "⛽ Ціни на пальне (OKKO):\n"
        for fuel in prices:
            name = fuel.get("name")
            price = fuel.get("price")
            result += f"{name}: {price}₴\n"
        return result
    except Exception:
        return "⚠️ Не вдалося завантажити ціни на пальне."

# =======================
# Обробка команд
# =======================

@bot.message_handler(commands=["start", "help"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💵 Валюти")
    btn2 = types.KeyboardButton("₿ Криптовалюта")
    btn3 = types.KeyboardButton("⛽ Пальне")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Привіт 👋\nОберіть категорію:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "💵 Валюти":
        bot.send_message(message.chat.id, get_exchange_rates())
    elif message.text == "₿ Криптовалюта":
        bot.send_message(message.chat.id, get_crypto())
    elif message.text == "⛽ Пальне":
        bot.send_message(message.chat.id, get_fuel_prices())
    else:
        bot.send_message(message.chat.id, "Виберіть команду з меню.")

# =======================
# Flask Webhook
# =======================

@app.route("/webhook", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Бот працює ✅", 200

# =======================
# Головний запуск
# =======================

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    # Flask під Gunicorn (тому без app.run)
