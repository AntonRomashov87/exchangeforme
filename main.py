import os
import telebot
import requests
from flask import Flask, request

# =======================
# Flask
# =======================
app = Flask(__name__)

# --- Токен бота з Render Environment Variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не знайдений. Будь ласка, додайте його в налаштуваннях Render → Environment.")
    exit()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# --- API для валют ---
# Використовуємо NBU API, який є офіційним та надійним
EXCHANGE_API_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"

# --- API для криптовалюти ---
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"

# --- API для металів (XAU – золото, XAG – срібло, XPT – платина) ---
# Metals.live API є платним. Це лише приклад.
METALS_API_URL = "https://api.metals.live/v1/spot"

# --- API для пального (фіксовані дані як приклад) ---
def get_fuel_prices_data():
    """Повертає фіксовані ціни на пальне (як приклад, адаптований під Україну)"""
    return {
        "Дизель": 56.50,
        "А-95": 57.80,
        "А-92": 55.20
    }

# =======================
# Webhook URL
# =======================
WEBHOOK_URL = f"{os.getenv('RENDER_EXTERNAL_URL')}/webhook"

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
        usd = next(item for item in r if item["cc"] == "USD")["rate"]
        eur = next(item for item in r if item["cc"] == "EUR")["rate"]
        pln = next(item for item in r if item["cc"] == "PLN")["rate"]

        text = (
            f"💱 **Курс валют (до UAH)**\n\n"
            f"🇺🇸 USD: {usd:.2f}₴\n"
            f"🇪🇺 EUR: {eur:.2f}₴\n"
            f"🇵🇱 PLN: {pln:.2f}₴"
        )
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, "⚠️ Виникла помилка при отриманні курсу валют.")
        print(f"Помилка в exchange(): {e}")

# --- Топ-10 криптовалют ---
@bot.message_handler(commands=["crypto"])
def crypto(message):
    try:
        params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
        data = requests.get(CRYPTO_API_URL, params=params).json()

        text = "₿ **Топ-10 криптовалют**\n\n"
        for coin in data:
            # Використовуємо .get() для безпечного доступу до словника
            price_change = coin.get('price_change_percentage_24h', 0)
            text += f"**{coin['market_cap_rank']}. {coin['symbol'].upper()}**: {coin['current_price']:.2f}$ (💹 {price_change:.2f}%)\n"

        bot.reply_to(message, text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Виникла помилка при отриманні даних про криптовалюту.")
        print(f"Помилка в crypto(): {e}")

# --- Метали ---
@bot.message_handler(commands=["metals"])
def metals(message):
    try:
        metals_data = requests.get(METALS_API_URL).json()
        # Оскільки API повертає список словників, використовуємо dict comprehension для зручності
        metals_dict = {list(item.keys())[0]: list(item.values())[0] for item in metals_data}
        
        text = (
            f"🥇 **Метали (USD/oz)**\n\n"
            f"Золото: {metals_dict.get('gold', 'N/A'):.2f}$\n"
            f"Срібло: {metals_dict.get('silver', 'N/A'):.2f}$\n"
            f"Платина: {metals_dict.get('platinum', 'N/A'):.2f}$\n"
            f"Паладій: {metals_dict.get('palladium', 'N/A'):.2f}$"
        )
        bot.reply_to(message, text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Виникла помилка при отриманні цін на метали.")
        print(f"Помилка в metals(): {e}")

# --- Пальне ---
@bot.message_handler(commands=["fuel"])
def fuel(message):
    try:
        fuel_prices = get_fuel_prices_data()
        text = "⛽ **Ціни на пальне (приклад):**\n\n"
        for k, v in fuel_prices.items():
            text += f"**{k}**: {v:.2f}₴\n"
        bot.reply_to(message, text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Не вдалося завантажити ціни на пальне.")
        print(f"Помилка в fuel(): {e}")

# --- Обробка webhook ---
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        print(f"Received webhook payload: {json_string}")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid content type', 403

# --- Тестова сторінка ---
@app.route("/", methods=["GET"])
def index():
    return "Бот працює через Webhook на Render Free!", 200

# --- Flask запуск ---
if __name__ == "__main__":
    if WEBHOOK_URL and bot.remove_webhook() and bot.set_webhook(url=WEBHOOK_URL):
        try:
            bot.remove_webhook()
            bot.set_webhook(url=WEBHOOK_URL)
            print(f"✅ Webhook встановлено на {WEBHOOK_URL}")
        except telebot.apihelper.ApiTelegramException as e:
            print(f"❌ Не вдалося встановити Webhook: {e}")
    else:
        print("❌ WEBHOOK_URL не знайдений. Запустити бот неможливо.")
    
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
