import os
import telebot
import requests
from flask import Flask, request

# --- Токен бота ---
BOT_TOKEN = '8008617718:AAHYtH1YadkHebM2r8MQrMnRadYLTXdf4WQ'

# --- Ваш ключ OpenExchangeRates ---
EXCHANGE_API_KEY = 'YOUR_OPENEXCHANGERATES_API_KEY'
EXCHANGE_API_URL = f"https://openexchangerates.org/api/latest.json?app_id={EXCHANGE_API_KEY}&symbols=UAH,USD,EUR,PLN"

# CoinGecko API
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# Flask та Telegram bot
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Автоматично видаляємо старий webhook ---
bot.remove_webhook()
print("Старий webhook видалено")

# --- Встановлення нового webhook для Render ---
WEBHOOK_URL = f"{os.environ.get('RENDER_EXTERNAL_URL')}/webhook"
bot.set_webhook(url=WEBHOOK_URL)
print(f"Новий webhook встановлено: {WEBHOOK_URL}")

# --- Команди /start та /help ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "Привіт! 👋 Я бот для перевірки курсів валют та криптовалюти.\n"
        "Команди:\n"
        "💰 /exchange - курс валют (USD, EUR, PLN до UAH)\n"
        "₿ /crypto - ціни BTC, ETH, USDT\n"
        "💡 /help - ця довідка"
    )
    bot.reply_to(message, welcome_text)

# --- Курс валют ---
@bot.message_handler(commands=['exchange'])
def get_exchange_rates(message):
    try:
        response = requests.get(EXCHANGE_API_URL)
        data = response.json()
        usd_to_base = data['rates']['UAH']
        eur_to_base = usd_to_base / data['rates']['EUR']
        pln_to_base = usd_to_base / data['rates']['PLN']
        exchange_text = (
            f"💰 **Курс валют (до UAH)**:\n"
            f"🇺🇸 USD: {usd_to_base:.2f} грн\n"
            f"🇪🇺 EUR: {eur_to_base:.2f} грн\n"
            f"🇵🇱 PLN: {pln_to_base:.2f} грн"
        )
        bot.reply_to(message, exchange_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Помилка при отриманні курсу валют.")
        print(f"Помилка валют: {e}")

# --- Ціни на криптовалюту ---
@bot.message_handler(commands=['crypto'])
def get_crypto_prices(message):
    try:
        params = {'ids':'bitcoin,ethereum,tether','vs_currencies':'usd,uah'}
        response = requests.get(CRYPTO_API_URL, params=params)
        data = response.json()
        btc_usd, btc_uah = data['bitcoin']['usd'], data['bitcoin']['uah']
        eth_usd, eth_uah = data['ethereum']['usd'], data['ethereum']['uah']
        usdt_usd, usdt_uah = data['tether']['usd'], data['tether']['uah']

        crypto_text = (
            f"₿ **Ціни на криптовалюту**:\n\n"
            f"📊 BTC: {btc_usd:,} $ / {btc_uah:,.0f} грн\n"
            f"📊 ETH: {eth_usd:,} $ / {eth_uah:,.0f} грн\n"
            f"📊 USDT: {usdt_usd} $ / {usdt_uah:.2f} грн"
        )
        bot.reply_to(message, crypto_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Помилка при отриманні цін криптовалюти.")
        print(f"Помилка криптовалюти: {e}")

# --- Endpoint webhook для Telegram ---
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# --- Тестова сторінка для Render ---
@app.route("/", methods=['GET'])
def index():
    return "Bot is running via Webhook on Render!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
