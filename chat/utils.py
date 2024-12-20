import telebot
import logging
import os

from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

def send_telegram_message(user_telegram_id, message):
    try:
        bot.send_message(user_telegram_id, message)
    except Exception as e:
        logging.error(f"Не вдалося надіслати повідомлення: {e}")
