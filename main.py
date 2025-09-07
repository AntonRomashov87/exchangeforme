import telebot
import requests

# --- Встав свій токен сюди ---
BOT_TOKEN = '8008617718:AAHYtH1YadkHebM2r8MQrMnRadYLTXdf4WQ'

# Замініть 'YOUR_OPENEXCHANGERATES_API_KEY' на ваш ключ API
EXCHANGE_API_KEY = 'YOUR_OPENEXCHANGERATES_API_KEY'
EXCHANGE_API_URL = f"https://openexchangerates.org/api/latest.json?app_id={EXCHANGE_API_KEY}&symbols=UAH,USD,EUR,PLN"

# CoinGecko API для отримання цін на криптовалюту
CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "Привіт! 👋 Я бот для перевірки курсів валют та цін на криптовалюту.\n"
        "Ось мої команди:\n\n"
        "💰 /exchange - отримати курс валют (USD, EUR, PLN до UAH)\n"
        "₿ /crypto - отримати ціни на основні криптовалюти (BTC, ETH, USDT)\n"
        "💡 /help - вивести цю довідку"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['exchange'])
def get_exchange_rates(message):
    try:
        response = requests.get(EXCHANGE_API_URL)
        data = response.json()

        usd_to_base = data['rates']['UAH']
        eur_to_base = data['rates']['UAH'] / data['rates']['EUR']
        pln_to_base = data['rates']['UAH'] / data['rates']['PLN']
        
        exchange_text = (
            f"💰 **Курс валют (до UAH)**:\n\n"
            f"🇺🇸 USD: {usd_to_base:.2f} грн\n"
            f"🇪🇺 EUR: {eur_to_base:.2f} грн\n"
            f"🇵🇱 PLN: {pln_to_base:.2f} грн"
        )
        bot.reply_to(message, exchange_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Виникла помилка при отриманні курсу валют. Спробуйте пізніше.")
        print(f"Помилка при отриманні курсу валют: {e}")

@bot.message_handler(commands=['crypto'])
def get_crypto_prices(message):
    try:
        params = {'ids': 'bitcoin,ethereum,tether','vs_currencies': 'usd,uah'}
        response = requests.get(CRYPTO_API_URL, params=params)
        data = response.json()

        btc_usd = data['bitcoin']['usd']
        btc_uah = data['bitcoin']['uah']
        eth_usd = data['ethereum']['usd']
        eth_uah = data['ethereum']['uah']
        usdt_usd = data['tether']['usd']
        usdt_uah = data['tether']['uah']

        crypto_text = (
            f"₿ **Ціни на криптовалюту**:\n\n"
            f"📊 **BTC (Bitcoin)**\n"
            f"└  {btc_usd:,} $\n"
            f"└  {btc_uah:,.0f} грн\n\n"
            f"📊 **ETH (Ethereum)**\n"
            f"└  {eth_usd:,} $\n"
            f"└  {eth_uah:,.0f} грн\n\n"
            f"📊 **USDT (Tether)**\n"
            f"└  {usdt_usd} $\n"
            f"└  {usdt_uah:.2f} грн"
        )
        bot.reply_to(message, crypto_text, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "⚠️ Виникла помилка при отриманні цін на криптовалюту. Спробуйте пізніше.")
        print(f"Помилка при отриманні цін на криптовалюту: {e}")

if __name__ == '__main__':
    print("Бот запущено...")
    bot.infinity_polling()
