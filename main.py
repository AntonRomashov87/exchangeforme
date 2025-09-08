import os
import telebot
import requests
from flask import Flask, request
from telebot import types

# --- Токен бота ---
BOT_TOKEN = '8008617718:AAHYtH1YadkHebM2r8MQrMnRadYLTXdf4WQ'

# --- API для валют ---
EXCHANGE_API_URL = "https://api.exchangerate.host/latest?base=USD&symbols=UAH,EUR,PLN"

# CoinGecko API для криптовалюти
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# --- Ініціалізація бота та Flask ---
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Видаляємо старий webhook і встановлюємо новий ---
bot.remove_webhook()
print("Старий webhook видалено")

WEBHOOK_URL = f"{os.environ.get('RENDER_EXTERNAL_URL')}/webhook"
bot.set_webhook(url=WEBHOOK_URL)
print(f"Новий webhook встановлено: {WEBHOOK_URL}")

# --- Команди /start та /help з кнопками ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "Привіт! 👋 Я бот для перевірки курсів валют, криптовалюти та цін на пальне.\n"
        "Виберіть команду нижче або введіть її вручну:"
    )

    # Створюємо клавіатуру
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("💰 Курс валют", "₿ Крипто BTC/ETH/USDT")
    keyboard.row("₿ Топ-10 криптовалют", "⛽ Ціни на пальне")

    bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard)

# --- Обробник кнопок ---
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    text = message.text
    if text == "💰 Курс валют":
        get_exchange_rates(message)
    elif text == "₿ Крипто BTC/ETH/USDT":
        get_crypto_prices(message)
    elif text == "₿ Топ-10 криптовалют":
        get_top10_crypto(message)
    elif text == "⛽ Ціни на пальне":
        get_fuel_prices(message)

# --- Курс валют з емодзі ---
def get_exchange_rates(message):
    try:
        response = requests.get(EXCHANGE_API_URL)
        data = response.json()

        usd_to_uah = data['rates']['UAH']
        eur_to_uah = usd_to_uah / data['rates']['EUR']
        pln_to_uah = usd_to_uah / data['rates']['PLN']

        exchange_text = (
            f"💱 **Курс валют (до UAH)**\n\n"
            f"🇺🇸 USD: {usd_to_uah:,.2f} грн\n"
            f"🇪🇺 EUR: {eur_to_uah:,.2f} грн\n"
            f"🇵🇱 PLN: {pln_to_uah:,.2f} грн"
        )
        bot.reply_to(message, exchange_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Не вдалося отримати курс валют. Спробуйте пізніше.")
        print(f"Помилка валют: {e}")

# --- Ціни на 3 криптовалюти з емодзі ---
def get_crypto_prices(message):
    try:
        params = {'ids':'bitcoin,ethereum,tether','vs_currencies':'usd,uah'}
        response = requests.get(CRYPTO_API_URL, params=params)
        data = response.json()

        crypto_text = (
            f"₿ **Ціни на криптовалюту**\n\n"
            f"📊 BTC: {data['bitcoin']['usd']:.2f}$ / {data['bitcoin']['uah']:.0f} грн\n"
            f"🟣 ETH: {data['ethereum']['usd']:.2f}$ / {data['ethereum']['uah']:.0f} грн\n"
            f"🟢 USDT: {data['tether']['usd']:.2f}$ / {data['tether']['uah']:.2f} грн"
        )
        bot.reply_to(message, crypto_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Не вдалося отримати ціни криптовалюти. Спробуйте пізніше.")
        print(f"Помилка криптовалюти: {e}")

# --- Топ-10 криптовалют з емодзі ---
def get_top10_crypto(message):
    try:
        top10 = {
            "bitcoin": "₿",
            "ethereum": "🟣",
            "tether": "🟢",
            "binancecoin": "🟡",
            "usd-coin": "💵",
            "ripple": "💧",
            "cardano": "🔵",
            "solana": "🌊",
            "dogecoin": "🐶",
            "polkadot": "⚫"
        }
        params = {'ids': ','.join(top10.keys()), 'vs_currencies':'usd,uah'}
        response = requests.get(CRYPTO_API_URL, params=params)
        data = response.json()

        text = "₿ **Топ-10 криптовалют**\n\n"
        for coin, emoji in top10.items():
            prices = data.get(coin)
            if prices:
                text += f"{emoji} {coin.upper()}: {prices['usd']:.2f}$ / {prices['uah']:.0f} грн\n"

        bot.reply_to(message, text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Не вдалося отримати топ-10 криптовалют.")
        print(f"Помилка топ-10 криптовалют: {e}")

# --- Ціни на пальне з емодзі (середні ціни) ---
def get_fuel_prices(message):
    try:
        diesel = 57.0
        petrol = 53.0
        gas = 27.0

        fuel_text = (
            f"⛽ **Ціни на пальне в Україні**\n\n"
            f"🛢 Дизель: {diesel:.2f} грн/л\n"
            f"⛽ Бензин: {petrol:.2f} грн/л\n"
            f"💨 Газ: {gas:.2f} грн/л"
        )
        bot.reply_to(message, fuel_text)
    except Exception as e:
        bot.reply_to(message, "⚠️ Не вдалося отримати ціни на пальне.")
        print(f"Помилка пального: {e}")

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
