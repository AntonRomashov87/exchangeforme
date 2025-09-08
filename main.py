import os
import requests
from flask import Flask, request
import telebot
from telebot import types

# =======================
# Токен Telegram (вставлений прямо)
# =======================
BOT_TOKEN = "8008617718:AAHYtH1YadkHebM2r8MQrMnRadYLTXdf4WQ"
WEBHOOK_URL = "https://exchangeforme.onrender.com/webhook"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# =======================
# Функції для отримання даних
# =======================
def get_exchange_rates():
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    try:
        data = requests.get(url, timeout=5).json()
        usd = next(item for item in data if item["cc"] == "USD")["rate"]
        eur = next(item for item in data if item["cc"] == "EUR")["rate"]
        pln = next(item for item in data if item["cc"] == "PLN")["rate"]
        return f"💵 USD: {usd:.2f}₴\n💶 EUR: {eur:.2f}₴\n🇵🇱 PLN: {pln:.2f}₴"
    except Exception as e:
        print("Error get_exchange_rates:", e)
        return "⚠️ Не вдалося завантажити курси валют."

def get_crypto():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
    try:
        data = requests.get(url, params=params, timeout=5).json()
        result = "₿ Топ-10 криптовалют:\n"
        for coin in data:
            result += f"{coin['symbol'].upper()}: {coin['current_price']}$\n"
        return result
    except Exception as e:
        print("Error get_crypto:", e)
        return "⚠️ Не вдалося завантажити криптовалюти."

def get_fuel_prices():
    try:
        fuel_data = {
            "Дизель": 56.50,
            "А-95": 57.80,
            "А-92": 55.20
        }
        result = "⛽ Ціни на пальне (OKKO):\n"
        for k, v in fuel_data.items():
            result += f"{k}: {v:.2f}₴\n"
        return result
    except Exception as e:
        print("Error get_fuel_prices:", e)
        return "⚠️ Не вдалося завантажити ціни на пальне."

# =======================
# Обробники команд
# =======================
@bot.message_handler(commands=["start", "help"])
def start(message):
    print("Received /start or /help:", message)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("💵 Валюти")
    btn2 = types.KeyboardButton("₿ Криптовалюта")
    btn3 = types.KeyboardButton("⛽ Пальне")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Привіт 👋\nОберіть категорію:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print("Received message:", message)
    if not hasattr(message, "text") or not message.text:
        print("No text in message")
        return
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
    try:
        json_str = request.get_data().decode("UTF-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        print("Webhook processing error:", e)
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Бот працює ✅", 200

# =======================
# Запуск
# =======================
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"Webhook встановлено: {WEBHOOK_URL}")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
