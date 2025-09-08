# =======================
# Імпорти бібліотек
# =======================
import os  # Для доступу до змінних оточення (секретний токен)
import requests # Для HTTP-запитів до API
import logging # Для запису логів про помилки та роботу бота
from flask import Flask, request # Для створення веб-сервера (webhook)
import telebot # Основна бібліотека для роботи з Telegram Bot API
from telebot import types

# =======================
# Налаштування логування та базові конфігурації
# =======================

# Налаштування логування, щоб бачити інформацію про роботу та помилки в логах Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Безпека: Завантаження токена зі змінних оточення ---
# Перейдіть до налаштувань вашого сервісу на Render -> Environment
# Створіть змінну з назвою BOT_TOKEN і вставте туди ваш токен.
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Ініціалізація ---
if not BOT_TOKEN:
    logging.critical("ПОМИЛКА ЗАПУСКУ: Не знайдено змінну оточення BOT_TOKEN!")
    # Якщо токен не знайдено, бот не зможе запуститися.

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# =======================
# Блок 1: Функції отримання даних з API
# =======================

def get_exchange_rates():
    """
    Отримує курси валют (USD, EUR, PLN) з API Національного банку України.
    Включає обробку помилок таймауту та структури JSON.
    """
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    try:
        response = requests.get(url, timeout=10)
        # Генерує виняток, якщо сервер відповів помилкою (наприклад, 500, 404)
        response.raise_for_status() 
        data = response.json()
        
        # Створюємо словник курсів для зручності
        rates = {item['cc']: item['rate'] for item in data if item['cc'] in ["USD", "EUR", "PLN"]}
        
        # Формуємо рядок відповіді. Використовуємо .get() для безпечного доступу.
        usd_rate = rates.get("USD", 0)
        eur_rate = rates.get("EUR", 0)
        pln_rate = rates.get("PLN", 0)

        if not all([usd_rate, eur_rate, pln_rate]):
             logging.warning("API НБУ не повернуло одну з валют (USD/EUR/PLN).")
             return "⚠️ Частина даних про валюти тимчасово недоступна."

        result = f"Курс НБУ:\n" \
                 f"💵 USD: {usd_rate:.2f} ₴\n" \
                 f"💶 EUR: {eur_rate:.2f} ₴\n" \
                 f"🇵🇱 PLN: {pln_rate:.2f} ₴"
        return result

    except requests.exceptions.Timeout:
        logging.warning("NBU API request timed out.")
        return "⚠️ Сервер НБУ не відповідає. Спробуйте, будь ласка, за хвилину."
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error while getting exchange rates: {e}")
        return "⚠️ Помилка мережі при отриманні курсів. Спробуйте пізніше."
    except Exception as e:
        logging.error(f"Unhandled error in get_exchange_rates: {e}")
        return "⚠️ Виникла непередбачувана помилка сервера. Вже працюємо над вирішенням."

def get_crypto():
    """
    Отримує топ-5 криптовалют з API CoinGecko.
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 5, "page": 1}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = "₿ Топ-5 криптовалют (за даними CoinGecko):\n"
        for i, coin in enumerate(data):
            symbol = coin.get('symbol', 'N/A').upper()
            price = coin.get('current_price', 0)
            result += f"{i+1}. {symbol}: ${price:,.2f}\n" # Додано форматування тисяч
        return result
        
    except requests.exceptions.RequestException as e:
        logging.error(f"CoinGecko API request error: {e}")
        return "⚠️ Не вдалося завантажити дані про криптовалюти. Спробуйте пізніше."
    except Exception as e:
        logging.error(f"Unhandled error in get_crypto: {e}")
        return "⚠️ Виникла непередбачувана помилка сервера."

def get_fuel_prices():
    """
    Повертає статичні ціни на пальне. 
    Це надійний метод, оскільки не залежить від зовнішніх API, 
    які можуть часто змінюватися або блокувати запити.
    """
    # Для оновлення цін достатньо змінити значення тут і перезавантажити код на Render.
    fuel_data = {
        "⛽ A-95+": 59.99,
        "⛽ A-95": 57.49,
        "⛽ ДП": 55.99,
    }
    result = "⛽ Орієнтовні ціни на пальне:\n"
    for fuel_type, price in fuel_data.items():
        result += f"{fuel_type}: {price:.2f} ₴\n"
    return result

# =======================
# Блок 2: Обробники команд Telegram
# =======================

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    """Обробник команди /start. Створює клавіатуру."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("💵 Валюти")
    btn2 = types.KeyboardButton("₿ Криптовалюта")
    btn3 = types.KeyboardButton("⛽ Пальне")
    markup.add(btn1, btn2, btn3)
    
    welcome_text = "Привіт 👋\nЯ допоможу дізнатися актуальні курси.\nОберіть категорію:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обробляє натискання кнопок та текстові повідомлення."""
    chat_id = message.chat.id
    
    if message.text == "💵 Валюти":
        # Оптимізація: миттєва відповідь + редагування
        msg = bot.send_message(chat_id, "⏳ Отримую актуальні курси від НБУ...")
        rates_text = get_exchange_rates()
        bot.edit_message_text(rates_text, chat_id, msg.message_id)

    elif message.text == "₿ Криптовалюта":
        # Оптимізація: миттєва відповідь + редагування
        msg = bot.send_message(chat_id, "⏳ Завантажую дані з бірж...")
        crypto_text = get_crypto()
        bot.edit_message_text(crypto_text, chat_id, msg.message_id)

    elif message.text == "⛽ Пальне":
        # Запит миттєвий (статичні дані), тому редагування не потрібне
        bot.send_message(chat_id, get_fuel_prices())
        
    else:
        bot.send_message(chat_id, "Будь ласка, виберіть одну з опцій у меню нижче.")

# =======================
# Блок 3: Flask Webhook для Render
# =======================

@app.route("/", methods=["GET"])
def index():
    """Сторінка для перевірки стану (health check) сервісом Render."""
    return "Bot server is alive and running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Приймає оновлення (повідомлення від користувачів) від Telegram."""
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode("UTF-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "ok", 200
    else:
        return "Unsupported Media Type", 415

# Примітка: Блок `if __name__ == "__main__":` не потрібен, 
# оскільки Render використовує Gunicorn для запуску `app`.
