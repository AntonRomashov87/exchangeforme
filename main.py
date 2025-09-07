import os
import telebot
import requests
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Токен бота ---
BOT_TOKEN = '8008617718:AAHYtH1YadkHebM2r8MQrMnRadYLTXdf4WQ'

# --- API для валют ---
EXCHANGE_API_URL = "https://api.exchangerate.host/latest?base=USD&symbols=UAH,EUR,PLN"

# CoinGecko API для криптовалюти
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# Ціни на пальне (можна замінити на реальний API)
FUEL_PRICES = {'Бензин': 53.50, 'Дизель': 51.20, 'Газ': 28.70}

# --- Ініціалізація бота та Flask ---
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Видаляємо старий webhook і встановлюємо новий ---
bot.remove_webhook()
WEBHOOK_URL = f"{os.environ.get('RENDER_EXTERNAL_URL')}/webhook"
bot.set_webhook(url=WEBHOOK_URL)

# --- Старт і кнопки ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = "Привіт! 👋 Оберіть опцію:"
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("💰 Валюти", callback_data="exchange"),
        InlineKeyboardButton("₿ Крипта", callback_data="crypto"),
        InlineKeyboardButton("⛽ Паливо", callback_data="fuel")
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

# --- Callback для кнопок ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "exchange":
        send_exchange_options(call.message)
    elif call.data == "crypto":
        send_crypto_options(call.message)
    elif call.data == "fuel":
        send_fuel_prices(call.message)
    elif call.data in ["USD", "EUR", "PLN"]:
        send_single_currency(call.message, call.data)
    elif call.data in ["BTC", "ETH", "USDT"]:
        send_single_crypto(call.message, call.data)
    elif call.data in ["Бензин", "Дизель", "Газ"]:
        send_single_fuel(call.message, call.data)

# --- Вибір валют ---
def send_exchange_options(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🇺🇸 USD", callback_data="USD"),
        InlineKeyboardButton("🇪🇺 EUR", callback_data="EUR"),
        InlineKeyboardButton("🇵🇱 PLN", callback_data="PLN")
    )
    bot.send_message(message.chat.id, "Оберіть валюту:", reply_markup=markup)

def send_single_currency(message, currency):
    try:
        response = requests.get(EXCHANGE_API_URL)
        data = response.json()
        usd_to_uah = data['rates']['UAH']
        if currency == "USD":
            text = f"🇺🇸 USD → UAH: {usd_to_uah:,.2f} грн"
        elif currency == "EUR":
            eur_to_uah = usd_to_uah / data['rates']['EUR']
            text = f"🇪🇺 EUR → UAH: {eur_to_uah:,.2f} грн"
        elif currency == "PLN":
            pln_to_uah = usd_to_uah / data['rates']['PLN']
            text = f"🇵🇱 PLN → UAH: {pln_to_uah:,.2f} грн"
        bot.send_message(message.chat.id, text)
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Не вдалося отримати курс валют.")
        print(f"Помилка валют: {e}")

# --- Вибір крипти ---
def send_crypto_options(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("₿ BTC", callback_data="BTC"),
        InlineKeyboardButton("ETH", callback_data="ETH"),
        InlineKeyboardButton("USDT", callback_data="USDT")
    )
    bot.send_message(message.chat.id, "Оберіть криптовалюту:", reply_markup=markup)

def send_single_crypto(message, crypto):
    try:
        params = {'ids':'bitcoin,ethereum,tether','vs_currencies':'usd,uah'}
        response = requests.get(CRYPTO_API_URL, params=params)
        data = response.json()
        if crypto == "BTC":
            text = f"₿ BTC: {data['bitcoin']['usd']:,.2f} $ / {data['bitcoin']['uah']:,.0f} грн"
        elif crypto == "ETH":
            text = f"ETH: {data['ethereum']['usd']:,.2f} $ / {data['ethereum']['uah']:,.0f} грн"
        elif crypto == "USDT":
            text = f"USDT: {data['tether']['usd']:,.2f} $ / {data['tether']['uah']:,.2f} грн"
        bot.send_message(message.chat.id, text)
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Не вдалося отримати ціни криптовалюти.")
        print(f"Помилка крипти: {e}")

# --- Ціни на пальне ---
def send_fuel_prices(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Бензин", callback_data="Бензин"),
        InlineKeyboardButton("Дизель", callback_data="Дизель"),
        InlineKeyboardButton("Газ", callback_data="Газ")
    )
    bot.send_message(message.chat.id, "Оберіть вид палива:", reply_markup=markup)

def send_single_fuel(message, fuel_type):
    price = FUEL_PRICES.get(fuel_type)
    if price:
        bot.send_message(message.chat.id, f"{fuel_type}: {price:,.2f} грн/л")
    else:
        bot.send_message(message.chat.id, "Ціна не знайдена.")

# --- Webhook endpoint для Telegram ---
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# --- Тестова сторінка ---
@app.route("/", methods=['GET'])
def index():
    return "Bot is running via Webhook on Render!", 200

# --- Запуск Flask ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
