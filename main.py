import os
import telebot
import requests
from flask import Flask, request

# --- Токен бота ---
BOT_TOKEN = '8008617718:AAHYtH1YadkHebM2r8MQrMnRadYLTXdf4WQ'

# --- API для валют ---
EXCHANGE_API_URL = "https://api.exchangerate.host/latest?base=USD&symbols=UAH,EUR,PLN"

# CoinGecko API для криптовалюти
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# API для пального (приклад, можна змінити на актуальний)
FUEL_API_URL = "https://api.collectapi.com/gasPrice/ukraineCityPrice"

# --- Ініціалізація бота та Flask ---
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Видаляємо старий webhook і встановлюємо новий ---
bot.remove_webhook()
print("Старий webhook видалено")

WEBHOOK_URL = f"{os.environ.get('RENDER_EXTERNAL_URL')}/webhook"
bot.set_webhook(url=WEBHOOK_URL)
print(f"Новий webhook встановлено: {WEBHOOK_URL}")

# --- Команди /start та /help ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "Привіт! 👋 Я бот для перевірки курсів валют, криптовалюти та цін на пальне.\n"
        "Команди:\n"
        "💰 /exchange - курс валют (USD, EUR, PLN → UAH)\n"
        "₿ /crypto - ціни BTC, ETH, USDT\n"
        "₿ /crypto10 - топ-10 криптовалют (USD, UAH)\n"
        "⛽ /fuel - ціни на пальне (дизель, бензин, газ)\n"
        "💡 /help - ця довідка"
    )
    bot.reply_to(message, welcome_text)

# --- Курс валют ---
@bot.message_handler(commands=['exchange'])
def get_exchange_rates(message):
    try:
        response = requests.get(EXCHANGE_API_URL)
        data = response.json()

        usd_to_uah = data['rates']['UAH']
        eur_to_uah = usd_to_uah / data['rates']['EUR']
        pln_to_uah = usd_to_uah / data['rates']['PLN']

        exchange_text = (
            f"💰 **Курс валют (до UAH)**:\n"
            f"🇺🇸 USD: {usd_to_uah:,.2f} грн\n"
            f"🇪🇺 EUR: {eur_to_uah:,.2f} грн\n"
            f"🇵🇱 PLN: {pln_to_uah:,.2f} грн"
        )
        bot.reply_to(message, exchange_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Не вдалося отримати курс валют. Спробуйте пізніше.")
        print(f"Помилка валют: {e}")

# --- Ціни на 3 криптовалюти ---
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
            f"📊 BTC: {btc_usd:,.2f} $ / {btc_uah:,.0f} грн\n"
            f"📊 ETH: {eth_usd:,.2f} $ / {eth_uah:,.0f} грн\n"
            f"📊 USDT: {usdt_usd:,.2f} $ / {usdt_uah:,.2f} грн"
        )
        bot.reply_to(message, crypto_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Не вдалося отримати ціни криптовалюти. Спробуйте пізніше.")
        print(f"Помилка криптовалюти: {e}")

# --- Топ-10 криптовалют ---
@bot.message_handler(commands=['crypto10'])
def get_top10_crypto(message):
    try:
        top10 = "bitcoin,ethereum,tether,binancecoin,usd-coin,ripple,cardano,solana,dogecoin,polkadot"
        params = {'ids': top10, 'vs_currencies':'usd,uah'}
        response = requests.get(CRYPTO_API_URL, params=params)
        data = response.json()

        text = "₿ **Топ-10 криптовалют**:\n\n"
        for coin, prices in data.items():
            text += f"{coin.upper()}: {prices['usd']:.2f}$ / {prices['uah']:.0f} грн\n"

        bot.reply_to(message, text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Не вдалося отримати топ-10 криптовалют.")
        print(f"Помилка топ-10 криптовалют: {e}")

# --- Ціни на пальне ---
@bot.message_handler(commands=['fuel'])
def get_fuel_prices(message):
    try:
        # Приклад з API collectapi.com (потрібен ключ)
        headers = {"Authorization": "apikey YOUR_COLLECTAPI_KEY"}
        response = requests.get(FUEL_API_URL, headers=headers)
        data = response.json()

        # Припустимо, у JSON є fields: diesel, petrol, gas
        diesel = data['result']['diesel']
        petrol = data['result']['petrol']
        gas = data['result']['gas']

        fuel_text = (
            f"⛽ **Ціни на пальне в Україні**:\n"
            f"🛢 Дизель: {diesel} грн/л\n"
            f"⛽ Бензин: {petrol} грн/л\n"
            f"💨 Газ: {gas} грн/л"
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
