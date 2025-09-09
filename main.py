import os
import telebot
import requests
from flask import Flask, request

# --- Токен бота з Render Environment Variables ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не знайдений! Додай його у Render → Environment.")

bot = telebot.TeleBot(BOT_TOKEN)

# --- API для валют ---
EXCHANGE_API_URL = "https://api.exchangerate.host/latest?base=USD&symbols=UAH,EUR,PLN"

# --- API для криптовалюти ---
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# --- API для металів (XAU – золото, XAG – срібло, XPT – платина, XPD – паладій) ---
METALS_API_URL = "https://api.metals.live/v1/spot"

# --- API для пального (ціни в Україні, в євро/доларах) ---
FUEL_API_URL = "https://api.e-control.at/sprit/preise"

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
        "₿ /crypto — топ-10 криптовалют\n"
        "🥇 /metals — ціни на метали\n"
        "⛽ /fuel — ціни на бензин і дизель\n"
    )


# --- Курс валют ---
@bot.message_handler(commands=["exchange"])
def exchange(message):
    try:
        r = requests.get(EXCHANGE_API_URL).json()
        usd = r["rates"]["UAH"]
        eur = r["rates"]["UAH"] / r["rates"]["EUR"]
        pln = r["rates"]["UAH"] / r["rates"]["PLN"]

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


# --- Топ-10 криптовалют ---
@bot.message_handler(commands=["crypto"])
def crypto(message):
    try:
        params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
        data = requests.get("https://api.coingecko.com/api/v3/coins/markets", params=params).json()

        text = "₿ Топ-10 криптовалют\n\n"
        for coin in data:
            text += f"{coin['symbol'].upper()} — {coin['current_price']}$ (💹 {coin['price_change_percentage_24h']:.2f}%)\n"

        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, "⚠️ Помилка отримання криптовалют.")
        print(e)


# --- Метали ---
@bot.message_handler(commands=["metals"])
def metals(message):
    try:
        metals = requests.get(METALS_API_URL).json()
        # Формат: [{"gold": price}, {"silver": price}, {"platinum": price}, {"palladium": price}]
        text = (
            f"🥇 Метали (USD/oz)\n\n"
            f"Золото: {metals[0]['gold']}$\n"
            f"Срібло: {metals[1]['silver']}$\n"
            f"Платина: {metals[2]['platinum']}$\n"
            f"Паладій: {metals[3]['palladium']}$"
        )
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, "⚠️ Помилка отримання металів.")
        print(e)


# --- Пальне ---
@bot.message_handler(commands=["fuel"])
def fuel(message):
    try:
        # Це API австрійського контролю пального (демо), дані можна адаптувати під укр. джерела
        data = requests.get(FUEL_API_URL).json()
        # Для прикладу витягаємо кілька
        diesel = data[0]["sorte"] + " — " + str(data[0]["preis"]) + " €/L"
        petrol = data[1]["sorte"] + " — " + str(data[1]["preis"]) + " €/L"

        text = f"⛽ Ціни на пальне\n\n{diesel}\n{petrol}"
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, "⚠️ Помилка отримання даних про пальне.")
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
