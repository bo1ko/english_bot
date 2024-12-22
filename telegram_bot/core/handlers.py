from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.types import Message

import django_setup
from telegram_bot.core import db_request
from telegram_bot.core.middlewares import CheckAndAddUserMiddleware
from telegram_bot.core.websocket_request import send_to_websocket


# routers
router = Router()
router.message.middleware(CheckAndAddUserMiddleware())


# handlers
@router.message(CommandStart())
async def cmd_start(message: Message):
    await db_request.create_system_action(
        await db_request.get_telegram_user(message.from_user.id), "/start"
    )
    await message.answer("👋")


@router.message(F.text & ~F.command)
async def handle_text_message(message: Message):
    obj_tg_user = await db_request.get_telegram_user(message.from_user.id)
    await db_request.create_system_action(obj_tg_user, message.text)

    obj_chat, chat_created = await db_request.get_or_create_communication_chat(obj_tg_user)

    if chat_created:
        await message.answer("Чат був створений. Ви можете почати спілкування.")
    elif chat_created is None:
        await message.answer("Не вдалося створити чат.")
        return

    user_id, message_created = await db_request.create_message(obj_tg_user, obj_chat, message.text)
    
    if message_created:
        socket_result = await send_to_websocket(obj_chat.pk, user_id, message.text)
    else:
        socket_result = False
    
    if message_created and socket_result:
        await message.answer("Ваше повідомлення було надіслано в адміністраторові.")
    else:
        await message.answer("Не вдалося надіслати повідомлення в адміністратора.")

