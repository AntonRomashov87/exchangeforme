import os
import telebot
import requests
from flask import Flask, request

# --- Токен бота ---
BOT_TOKEN = "ТВОЙ_ТОКЕН"
bot = telebot.TeleBot(BOT_TOKEN)

# --- API для валют ---
EXCHANGE_API_URL = "https://api.exchangerate.host/latest?base=USD&symbols=UAH,EUR,PLN"

# --- API для криптовалюти ---
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# --- API для ТОП-10 криптовалют ---
CRYPTO_TOP10_URL = "https://api.coingecko.com/api/v3/coins/markets"

# --- API для бензину/дизелю ---
FUEL_API_URL = "https://api.globalpetrolprices.com/gasoline_and_diesel_prices.json"  
# (тут безкоштовно показує загальні світові ціни)

# --- Flask ---
app = Flask(__name__)

# --- Webhook URL ---
WEBHOOK_URL = f"{os.environ.get('RENDER_EXTERNAL_URL')}/webhook"

# Встановлюємо webhook
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)


# --- Команда /start ---
@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.reply_to(
        message,
        "Привіт! 👋 Я бот на Render Free.\n\n"
        "Команди:\n"
        "💰 /exchange — курс валют\n"
        "₿ /crypto — BTC, ETH, USDT\n"
        "📊 /topcrypto — ТОП-10 криптовалют\n"
        "⛽ /fuel — ціни на бензин і дизель\n"
    )


# --- Курс валют ---
@bot.message_handler(commands=["exchange"])
def exchange(message):
    try:
        r = requests.get(EXCHANGE_API_URL).json()
        usd = r["rates"]["UAH"]
        eur = usd / r["rates"]["EUR"]
        pln = usd / r["rates"]["PLN"]

        text = (
            f"💱 Курс валют (до UAH)\n\n"
            f"🇺🇸 USD: {usd:.2f} грн\n"
            f"🇪🇺 EUR: {eur:.2f} грн\n"
            f"🇵🇱 PLN: {pln:.2f} грн"
        )
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, "⚠️ Помилка отримання курсу валют.")
        print(e)


# --- Ціни на криптовалюту (BTC/ETH/USDT) ---
@bot.message_handler(commands=["crypto"])
def crypto(message):
    try:
        params = {"ids": "bitcoin,ethereum,tether", "vs_currencies": "usd,uah"}
        data = requests.get(CRYPTO_API_URL, params=params).json()

        text = (
            f"₿ Ціни на криптовалюту\n\n"
            f"BTC: {data['bitcoin']['usd']}$ / {data['bitcoin']['uah']} грн\n"
            f"ETH: {data['ethereum']['usd']}$ / {data['ethereum']['uah']} грн\n"
            f"USDT: {data['tether']['usd']}$ / {data['tether']['uah']} грн"
        )
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, "⚠️ Помилка отримання криптовалют.")
        print(e)


# --- ТОП-10 криптовалют ---
@bot.message_handler(commands=["topcrypto"])
def topcrypto(message):
    try:
        params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
        data = requests.get(CRYPTO_TOP10_URL, params=params).json()

        text = "📊 ТОП-10 криптовалют за капіталізацією:\n\n"
        for coin in data:
            text += f"{coin['market_cap_rank']}. {coin['name']} ({coin['symbol'].upper()}): {coin['current_price']}$\n"
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, "⚠️ Помилка отримання ТОП криптовалют.")
        print(e)


# --- Ціни на бензин і дизель ---
@bot.message_handler(commands=["fuel"])
def fuel(message):
    try:
        data = requests.get(FUEL_API_URL).json()

        # Виберемо середні світові ціни
        gasoline = data["global"]["gasoline"]["usd_per_liter"]
        diesel = data["global"]["diesel"]["usd_per_liter"]

        text = (
            f"⛽ Середні ціни у світі:\n\n"
            f"Бензин: {gasoline:.2f} $/л\n"
            f"Дизель: {diesel:.2f} $/л"
        )
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, "⚠️ Помилка отримання цін на пальне.")
        print(e)


# --- Обробка webhook ---
@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "", 200


# --- Тестова сторінка ---
@app.route("/", methods=["GET"])
def index():
    return "Bot is running via Webhook on Render Free!", 200


# --- Flask запуск ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
