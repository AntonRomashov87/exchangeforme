import os
import telebot
import requests
from flask import Flask, request
import re # Імпортуємо модуль для роботи з регулярними виразами
from telebot import types # Імпортуємо типи для створення кнопок

# =======================
# Flask
# =======================
app = Flask(__name__)

# --- Токен бота з Railway Environment Variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не знайдений. Будь ласка, додайте його в налаштуваннях Railway → Variables.")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# =======================
# API URLs
# =======================

# --- API для валют (НБУ) ---
EXCHANGE_API_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"

# --- API для криптовалюти (CoinGecko) ---
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/coins/markets"

# --- Дані для пального (залишаємо як приклад) ---
def get_fuel_prices_data():
    """Повертає фіксовані ціни на пальне (як приклад, адаптований під Україну)"""
    return {
        "Дизель": 56.50,
        "А-95": 57.80,
        "А-92": 55.20
    }

# =======================
# Допоміжна функція для екранування Markdown
# =======================
def escape_markdown(text: str) -> str:
    """Екранує спеціальні символи для Telegram MarkdownV2."""
    escape_chars = r"[_*\[\]()~`>#\+\-=|{}.!]"
    return re.sub(f'({escape_chars})', r'\\\1', text)

# =======================
# Обробники команд та кнопок
# =======================

# --- Команда /start з'являється клавіатура ---
@bot.message_handler(commands=["start", "help"])
def start(message):
    print(f"Отримано команду /start від користувача {message.chat.id}")
    
    # Створюємо клавіатуру з кнопками
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("💰 Курс валют")
    btn2 = types.KeyboardButton("₿ Топ-10 криптовалют")
    btn3 = types.KeyboardButton("🥇 Ціни на метали")
    btn4 = types.KeyboardButton("⛽ Ціни на пальне")
    markup.add(btn1, btn2, btn3, btn4)

    text = "Привіт\\! 👋 Я бот\\-помічник\\.\n\nОбери одну з опцій нижче:"
    
    # Відправляємо повідомлення з кнопками
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='MarkdownV2')

# --- Обробник для кнопки "Курс валют" ---
@bot.message_handler(func=lambda message: message.text == "💰 Курс валют")
def exchange(message):
    try:
        r = requests.get(EXCHANGE_API_URL).json()
        usd_rate = next(item for item in r if item["cc"] == "USD")["rate"]
        eur_rate = next(item for item in r if item["cc"] == "EUR")["rate"]
        pln_rate = next(item for item in r if item["cc"] == "PLN")["rate"]

        usd_str = f"{usd_rate:.2f}".replace(".", "\\.")
        eur_str = f"{eur_rate:.2f}".replace(".", "\\.")
        pln_str = f"{pln_rate:.2f}".replace(".", "\\.")
        
        text = (
            f"💱 *Курс валют \\(до UAH\\)*\n\n"
            f"🇺🇸 USD: {usd_str}₴\n"
            f"🇪🇺 EUR: {eur_str}₴\n"
            f"🇵🇱 PLN: {pln_str}₴"
        )
        bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')
    except Exception as e:
        bot.send_message(message.chat.id, escape_markdown("⚠️ Не вдалося отримати курс валют."))
        print(f"Помилка в exchange(): {e}")

# --- Обробник для кнопки "Топ-10 криптовалют" ---
@bot.message_handler(func=lambda message: message.text == "₿ Топ-10 криптовалют")
def crypto(message):
    try:
        params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
        data = requests.get(CRYPTO_API_URL, params=params).json()

        text_lines = ["₿ *Топ\\-10 криптовалют*"]
        for coin in data:
            price = f"{coin['current_price']:.2f}".replace(".", "\\.")
            # ВИПРАВЛЕНО: Додано екранування знаку мінус (-)
            change = f"{coin.get('price_change_percentage_24h', 0):.2f}".replace(".", "\\.").replace("-", "\\-")
            line = (f"*{coin['market_cap_rank']}\\. {coin['symbol'].upper()}*: "
                    f"{price}\\$ \\(💹 {change}\\%\\)")
            text_lines.append(line)
        
        text = "\n".join(text_lines)
        bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')
    except Exception as e:
        bot.send_message(message.chat.id, escape_markdown("⚠️ Не вдалося отримати дані про криптовалюту."))
        print(f"Помилка в crypto(): {e}")

# --- Обробник для кнопки "Ціни на метали" ---
@bot.message_handler(func=lambda message: message.text == "🥇 Ціни на метали")
def metals(message):
    api_key = os.getenv("METALS_API_KEY")
    
    if not api_key:
        error_text = "⚠️ Ключ для API металів не налаштований. Будь ласка, додайте METALS_API_KEY у змінні середовища на Railway."
        bot.send_message(message.chat.id, escape_markdown(error_text))
        print("Помилка: METALS_API_KEY не знайдений.")
        return

    url = "https://api.apilayer.com/metals/latest?base=USD&symbols=XAU,XAG,XPT,XPD"
    headers = { "apikey": api_key }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        # ВИПРАВЛЕНО: Додано логування повної помилки від API
        if not data.get("success"):
            print(f"Помилка API металів: {data}") # Друкуємо повну відповідь для діагностики
            api_error_info = data.get("error", {}).get("info", "Невідома помилка API.")
            raise ValueError(api_error_info)

        rates = data['rates']
        gold_price = f"{rates.get('XAU', 0):.2f}".replace(".", "\\.")
        silver_price = f"{rates.get('XAG', 0):.2f}".replace(".", "\\.")
        platinum_price = f"{rates.get('XPT', 0):.2f}".replace(".", "\\.")
        palladium_price = f"{rates.get('XPD', 0):.2f}".replace(".", "\\.")
        
        text = (
            f"🥇 *Метали \\(USD/oz\\)*\n\n"
            f"Золото: {gold_price}\\$\n"
            f"Срібло: {silver_price}\\$\n"
            f"Платина: {platinum_price}\\$\n"
            f"Паладій: {palladium_price}\\$"
        )
        bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')
    except Exception as e:
        bot.send_message(message.chat.id, escape_markdown("⚠️ Не вдалося отримати ціни на метали."))
        print(f"Помилка в metals(): {e}")

# --- Обробник для кнопки "Ціни на пальне" ---
@bot.message_handler(func=lambda message: message.text == "⛽ Ціни на пальне")
def fuel(message):
    try:
        fuel_prices = get_fuel_prices_data()
        text_lines = ["⛽ *Ціни на пальне \\(приклад\\):*"]
        for k, v in fuel_prices.items():
            price = f"{v:.2f}".replace(".", "\\.")
            # ВИПРАВЛЕНО: Додано екранування дефісу в назві пального (А-95)
            escaped_k = k.replace("-", "\\-")
            text_lines.append(f"*{escaped_k}*: {price}₴")
        
        text = "\n".join(text_lines)
        bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')
    except Exception as e:
        bot.send_message(message.chat.id, escape_markdown("⚠️ Не вдалося завантажити ціни на пальне."))
        print(f"Помилка в fuel(): {e}")

# =======================
# Webhook
# =======================
RAILWAY_STATIC_URL = os.getenv("RAILWAY_STATIC_URL")
WEBHOOK_URL = f"https://{RAILWAY_STATIC_URL}/webhook" if RAILWAY_STATIC_URL else ""

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid content type', 403

@app.route("/", methods=["GET"])
def index():
    return "Бот працює через Webhook на Railway!", 200

# =======================
# Flask запуск
# =======================
if __name__ == "__main__":
    if WEBHOOK_URL:
        try:
            current_webhook = bot.get_webhook_info()
            if current_webhook.url != WEBHOOK_URL:
                bot.remove_webhook()
                bot.set_webhook(url=WEBHOOK_URL)
                print(f"✅ Webhook встановлено на {WEBHOOK_URL}")
            else:
                print("✅ Webhook вже встановлено.")
        except Exception as e:
            print(f"❌ Не вдалося встановити Webhook: {e}")
    else:
        print("⚠️ Змінна RAILWAY_STATIC_URL не знайдена. Webhook не встановлено.")
    
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

