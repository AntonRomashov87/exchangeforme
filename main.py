import requests
import os
import json
from flask import Flask, request
import telebot
from telebot import types

# =======================
# Telegram
# =======================
# Отримання токена з змінних середовища. Це безпечніше!
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Отримання URL вебхука з змінних середовища.
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# =======================
# Flask
# =======================
app = Flask(__name__)

# =======================
# Дані для валюти, крипти та пального
# =======================
def get_exchange_rates():
    """Отримує курси валют з API НБУ."""
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    try:
        data = requests.get(url, timeout=5).json()
        usd = next(item for item in data if item["cc"] == "USD")["rate"]
        eur = next(item for item in data if item["cc"] == "EUR")["rate"]
        pln = next(item for item in data if item["cc"] == "PLN")["rate"]
        return f"💵 **Курси валют (до UAH)**:\n🇺🇸 USD: {usd:.2f}₴\n🇪🇺 EUR: {eur:.2f}₴\n🇵🇱 PLN: {pln:.2f}₴"
    except Exception:
        return "⚠️ Не вдалося завантажити курси валют."

def get_crypto():
    """Отримує топ-10 криптовалют з CoinGecko."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
    try:
        data = requests.get(url, params=params, timeout=5).json()
        result = "₿ **Топ-10 криптовалют**:\n\n"
        for coin in data:
            result += f"{coin['market_cap_rank']}. {coin['symbol'].upper()}: {coin['current_price']:.2f}$\n"
        return result
    except Exception:
        return "⚠️ Не вдалося завантажити криптовалюту."

def get_fuel_prices():
    """Повертає фіксовані ціни на пальне (приклад)."""
    try:
        fuel_data = {
            "Дизель": 56.50,
            "А-95": 57.80,
            "А-92": 55.20
        }
        result = "⛽ **Ціни на пальне (OKKO):**\n"
        for k, v in fuel_data.items():
            result += f"{k}: {v:.2f}₴\n"
        return result
    except Exception:
        return "⚠️ Не вдалося завантажити ціни на пальне."

# =======================
# Обробники повідомлень
# =======================
@bot.message_handler(commands=["start", "help"])
def start(message):
    """Обробник команди /start. Створює клавіатуру."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💵 Валюти", "₿ Криптовалюта", "⛽ Пальне")
    bot.send_message(message.chat.id, "Привіт 👋\nОберіть категорію:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обробник повідомлень з клавіатури."""
    if message.text == "💵 Валюти":
        bot.send_message(message.chat.id, get_exchange_rates())
    elif message.text == "₿ Криптовалюта":
        bot.send_message(message.chat.id, get_crypto())
    elif message.text == "⛽ Пальне":
        bot.send_message(message.chat.id, get_fuel_prices())
    else:
        bot.send_message(message.chat.id, "Виберіть команду з меню.")

# =======================
# Webhook
# =======================
@app.route("/webhook", methods=["POST"])
def webhook():
    """Обробляє POST-запити від Telegram."""
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "ok", 200
    return "Error", 400

@app.route("/", methods=["GET"])
def index():
    """Показує, що бот працює."""
    return "Бот працює ✅", 200

# =======================
# Запуск
# =======================
if __name__ == "__main__":
    if BOT_TOKEN and WEBHOOK_URL:
        # Встановлення вебхука при старті застосунку
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"Webhook встановлено на {WEBHOOK_URL}")
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    else:
        print("BOT_TOKEN або WEBHOOK_URL не встановлені. Запустити бот неможливо.")
