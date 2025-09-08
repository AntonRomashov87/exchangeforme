import os
import re
import logging
import requests
from flask import Flask, request
import telebot
from telebot import types
from bs4 import BeautifulSoup

# ---------- Налаштування логування ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------- Змінні середовища ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("BOT_TOKEN не знайдено в змінних середовища. Додайте BOT_TOKEN у Render Environment.")
    raise SystemExit("BOT_TOKEN not set")

# Для Render: намагаємось отримати зовнішній URL (Render дає RENDER_EXTERNAL_URL або RENDER_EXTERNAL_HOSTNAME)
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL") or (f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}" if os.getenv('RENDER_EXTERNAL_HOSTNAME') else None)

# ---------- Ініціалізація ----------
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

# ---------- HTTP headers ----------
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ExchangeBot/1.0; +https://example.com)"
}

# ---------- Функції: Валюти (НБУ) ----------
def get_nbu_rates():
    """Повертає dict {'USD': rate, 'EUR': rate, 'PLN': rate} або None при помилці"""
    try:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
        r = requests.get(url, timeout=8, headers=DEFAULT_HEADERS)
        r.raise_for_status()
        data = r.json()
        result = {}
        for cur in ("USD", "EUR", "PLN"):
            item = next((x for x in data if x.get("cc") == cur), None)
            if item and "rate" in item:
                result[cur] = float(item["rate"])
            else:
                logging.warning(f"НБУ: відсутній курс для {cur}")
                result[cur] = None
        return result
    except Exception as e:
        logging.exception("Помилка завантаження курсів НБУ")
        return None

# ---------- Функції: Топ-10 криптовалют (CoinGecko) ----------
def get_top10_crypto():
    """Повертає список рядків з топ-10 крипто (символ, ціна usd, зміна 24h)"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1, "price_change_percentage": "24h"}
        r = requests.get(url, params=params, timeout=10, headers=DEFAULT_HEADERS)
        r.raise_for_status()
        data = r.json()
        lines = []
        for coin in data:
            sym = coin.get("symbol", "").upper()
            name = coin.get("name", "")
            price = coin.get("current_price")
            change = coin.get("price_change_percentage_24h")
            market_cap = coin.get("market_cap")
            if price is None:
                continue
            line = f"{sym} ({name}) — ${price:,.2f}"
            if change is not None:
                line += f" ({change:+.2f}% 24h)"
            if market_cap:
                line += f" | MCap ${market_cap:,.0f}"
            lines.append(line)
        return lines
    except Exception as e:
        logging.exception("Помилка отримання крипти з CoinGecko")
        return None

# ---------- Функції: Ціни пального ОККО з Minfin (scraping) ----------
def get_okko_fuel_prices():
    """
    Парсить Minfin index сторінку для ОККО.
    Повертає dict { 'A95': price, 'A92': price, 'Дизель': price, ... } або None при помилці.
    """
    url = "https://index.minfin.com.ua/ua/markets/fuel/tm/okko/"
    try:
        r = requests.get(url, timeout=10, headers=DEFAULT_HEADERS)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        # Шукаємо таблицю — робимо гнучкий пошук
        table = soup.select_one("table") or soup.find("table")
        if not table:
            logging.warning("Minfin: таблиця цін не знайдена")
            return None

        prices = {}
        rows = table.select("tr")
        for row in rows:
            cols = row.select("td")
            if len(cols) >= 2:
                name = cols[0].get_text(strip=True)
                price_text = cols[1].get_text(strip=True)
                # Витягаємо число (на випадок додаткового тексту)
                m = re.search(r"[\d\.,]+", price_text)
                if not m:
                    continue
                raw = m.group(0).replace(",", ".")
                try:
                    val = float(raw)
                except:
                    continue
                # Нормалізуємо назву
                name_norm = name.replace("\xa0", " ").strip()
                prices[name_norm] = val
        if not prices:
            logging.warning("Minfin: не знайдено жодної ціни після парсингу")
            return None
        return prices
    except Exception:
        logging.exception("Помилка парсингу Minfin для ОККО")
        return None

# ---------- Форматування повідомлень ----------
def format_currency_message(rates: dict):
    if not rates:
        return "⚠️ Не вдалося отримати курси валют."
    lines = ["💱 **Курси (НБУ)**"]
    for cur in ("USD", "EUR", "PLN"):
        rate = rates.get(cur)
        if rate is None:
            lines.append(f"{cur}: N/A")
        else:
            lines.append(f"{cur}: {rate:,.2f} грн")
    return "\n".join(lines)

def format_crypto_message(lines):
    if not lines:
        return "⚠️ Не вдалося отримати дані по криптовалютам."
    header = "🔥 **Топ-10 криптовалют (за капіталізацією)**\n"
    return header + "\n".join(lines)

def format_fuel_message(prices: dict):
    if not prices:
        return "⚠️ Не вдалося отримати ціни пального."
    lines = ["⛽ **Ціни ОККО (Minfin)**"]
    # Сортуємо популярні пальні у потрібному порядку, якщо є
    preferred = ["A-95", "A-95+","A-92","Дизель","Газ","A95","A95+"]
    for k in preferred:
        if k in prices:
            lines.append(f"{k}: {prices[k]:,.2f} грн/л")
    # Додаємо інші
    for name, val in prices.items():
        if name in preferred:
            continue
        lines.append(f"{name}: {val:,.2f} грн/л")
    return "\n".join(lines)

# ---------- Клавіатури / меню ----------
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("💵 Валюти", callback_data="menu_currency"),
        types.InlineKeyboardButton("🔥 Крипто", callback_data="menu_crypto"),
        types.InlineKeyboardButton("⛽ Пальне", callback_data="menu_fuel"),
    )
    return markup

def currency_buttons():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("USD", callback_data="cur_USD"),
        types.InlineKeyboardButton("EUR", callback_data="cur_EUR"),
        types.InlineKeyboardButton("PLN", callback_data="cur_PLN"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="menu_back")
    )
    return markup

def crypto_buttons():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Топ-10 (список)", callback_data="crypto_top10"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="menu_back")
    )
    return markup

def fuel_buttons():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Показати ціни ОККО", callback_data="fuel_okko"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="menu_back")
    )
    return markup

# ---------- Обробники команд ----------
@bot.message_handler(commands=["start", "help"])
def cmd_start(msg):
    txt = "Привіт! Оберіть категорію нижче:"
    bot.send_message(msg.chat.id, txt, reply_markup=main_menu())

# ---------- Callback handler ----------
@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    data = call.data
    chat_id = call.message.chat.id

    if data == "menu_currency":
        bot.send_message(chat_id, "Обрати валюту:", reply_markup=currency_buttons())

    elif data.startswith("cur_"):
        code = data.split("_", 1)[1]
        rates = get_nbu_rates()
        if not rates:
            bot.send_message(chat_id, "⚠️ Не вдалося отримати курси. Спробуйте пізніше.")
        else:
            r = rates.get(code)
            if r is None:
                bot.send_message(chat_id, f"{code}: N/A")
            else:
                bot.send_message(chat_id, f"{code} → UAH: {r:,.2f} грн")
        # не закриваємо клавіатуру автоматично

    elif data == "menu_crypto":
        bot.send_message(chat_id, "Криптовалюта:", reply_markup=crypto_buttons())

    elif data == "crypto_top10":
        crypto = get_top10_crypto()
        if not crypto:
            bot.send_message(chat_id, "⚠️ Не вдалося завантажити дані криптовалют.")
        else:
            # розбиваємо на частини щоб не перевищити ліміт повідомлення
            text = format_crypto_message(crypto)
            bot.send_message(chat_id, text, parse_mode="Markdown")
    
    elif data == "menu_fuel":
        bot.send_message(chat_id, "Пальне:", reply_markup=fuel_buttons())

    elif data == "fuel_okko":
        prices = get_okko_fuel_prices()
        if not prices:
            bot.send_message(chat_id, "⚠️ Не вдалося отримати ціни на пальне.")
        else:
            bot.send_message(chat_id, format_fuel_message(prices), parse_mode="Markdown")

    elif data == "menu_back":
        bot.send_message(chat_id, "Повертаю в меню", reply_markup=main_menu())

    else:
        bot.send_message(chat_id, f"Невідома команда: {data}")

# ---------- Webhook endpoint ----------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception:
        logging.exception("Помилка обробки webhook")
    return "", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running ✅", 200

# ---------- Запуск (встановлюємо webhook лише якщо знайшли URL) ----------
if __name__ == "__main__":
    # Ставимо webhook тільки коли Render надає зовнішній URL
    try:
        bot.remove_webhook()
    except Exception:
        logging.warning("remove_webhook() викликало помилку (ігноруємо)")

    if RENDER_EXTERNAL_URL:
        WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/webhook"
        try:
            bot.set_webhook(url=WEBHOOK_URL)
            logging.info(f"Webhook встановлено: {WEBHOOK_URL}")
        except Exception:
            logging.exception("Не вдалось встановити webhook")
    else:
        logging.warning("RENDER_EXTERNAL_URL / RENDER_EXTERNAL_HOSTNAME не знайдені — webhook не встановлено. Використовуйте Background Worker або задайте URL вручну.")

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
