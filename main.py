import os
import telebot

# Отримуємо токен з Environment Variables Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
print("BOT_TOKEN:", repr(BOT_TOKEN))  # Тимчасово для перевірки

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set or empty!")

# Створюємо бота
bot = telebot.TeleBot(BOT_TOKEN)

# Обробник команди /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привіт! Я твій бот 🚀")

# Обробник будь-якого текстового повідомлення
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ти написав: {message.text}")

# Запуск бота
bot.infinity_polling()
