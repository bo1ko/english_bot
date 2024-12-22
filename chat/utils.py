import telebot
import logging
import os

from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")


def send_sync_telegram_message(user_telegram_id, message):
    bot = telebot.TeleBot(API_TOKEN)

    try:
        bot.send_message(user_telegram_id, message)
    except Exception as e:
        logging.error(f"Не вдалося надіслати повідомлення: {e}")

async def send_async_telegram_message(chat_id: int, text: str):
    bot = Bot(token=API_TOKEN)
    
    try:
        sent_message = await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)
        message_id = sent_message.message_id
        
        return message_id
    except Exception as e:
        logging.error(f"Error sending message: {e}")