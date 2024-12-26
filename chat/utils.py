import telebot
import logging
import os

from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from dotenv import load_dotenv
from .models import TelegramUserAndAdminChat, StudentAndTeacherChat, TeacherAndAdminChat
from telegram_bot.core.keyboards import get_callback_btns

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
telebot_bot = telebot.TeleBot(API_TOKEN)
aiogram_bot = Bot(token=API_TOKEN)


def send_sync_telegram_message(user_telegram_id, message):
    try:
        telebot_bot.send_message(user_telegram_id, message)
        logging.info(f"Message sent {user_telegram_id}")
    except Exception as e:
        logging.error(f"Could not send message: {e}")


def edit_sync_telegram_message(chat_id: int, message_id: int, new_text: str):
    try:
        telebot_bot.edit_message_text(chat_id=chat_id,
                                      message_id=message_id,
                                      text=new_text,
                                      parse_mode="HTML")
        logging.info(f"Message edited: {chat_id} | {message_id}")
        return True
    except Exception as e:
        logging.error(f"Could not edit message: {e}")
        return False


def reply_sync_telegram_message(chat_id, message_id, reply_text):
    try:
        telebot_bot.send_message(chat_id,
                                 reply_text,
                                 reply_to_message_id=message_id,
                                 parse_mode="HTML")
        logging.info(f"Reply sent to message {message_id} in chat {chat_id}")
        return True
    except Exception as e:
        logging.error(f"Could not send reply: {e}")
        return False


async def send_async_alert_message(tg_id: int, role: str, from_user: str):
    try:
        await aiogram_bot.send_message(chat_id=tg_id,
                                       text=f"Вам прийшло нове повідомлення від {role} {from_user}.",
                                       parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Error sending alert message: {e}")


async def send_async_telegram_message(chat_id: int,
                                      text: str,
                                      reply_message_id: int = False):
    try:
        btns = {
            "Відповісти": f"admin",
        }
        if reply_message_id:
            sent_message = await aiogram_bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=reply_message_id,
                parse_mode=ParseMode.HTML,
                reply_markup=get_callback_btns(btns=btns))
        else:
            sent_message = await aiogram_bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=get_callback_btns(btns=btns),
            )
        message_id = sent_message.message_id

        return message_id
    except Exception as e:
        logging.error(f"Error sending message: {e}")
