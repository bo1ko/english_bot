from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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


class AdminMessage(StatesGroup):
    message = State()

class TeacherMessage(StatesGroup):
    message = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext, loop=False):
    if loop:
        await state.clear()
    else:
        await message.answer("Введіть повідомлення для адміністрації")
    
    await state.set_state(AdminMessage.message)

@router.message(AdminMessage.message)
async def cmd_admin_first(message: Message, state: FSMContext):
    chat_with = "telegram_user"
    obj_tg_user = await db_request.get_telegram_user(message.from_user.id)

    obj_chat, chat_created = await db_request.get_or_create_communication_chat(obj_tg_user, chat_with)

    if chat_created is None:
        await message.answer("Не вдалося створити чат.")
        return
    
    socket_result = await send_to_websocket(obj_chat.pk, obj_tg_user.pk, message.text, message.message_id, chat_with=chat_with)
    
    if socket_result:
        await message.answer("Ваше повідомлення було надіслано користувачу Telegram.")
        await cmd_admin(message, state, loop=True)
    else:
        await message.answer("Не вдалося надіслати повідомлення користувачу Telegram.")


@router.message(Command("teacher"))
async def cmd_teacher(message: Message, state: FSMContext, loop=False):
    if loop:
        await state.clear()
    else:
        await message.answer("Введіть повідомлення для вчителя")
    
    await state.set_state(TeacherMessage.message)

@router.message(TeacherMessage.message)
async def cmd_teacher_first(message: Message, state: FSMContext):
    chat_with = "student"
    obj_tg_user = await db_request.get_telegram_user(message.from_user.id)

    obj_chat, chat_created = await db_request.get_or_create_communication_chat(obj_tg_user, chat_with)

    if chat_created is None:
        await message.answer("Не вдалося створити чат.")
        return
    
    socket_result = await send_to_websocket(obj_chat.pk, obj_tg_user.pk, message.text, message.message_id, chat_with=chat_with)
    
    if socket_result:
        await message.answer("Ваше повідомлення було надіслано студенту.")
        await cmd_teacher(message, state, loop=True)
    else:
        await message.answer("Не вдалося надіслати повідомлення студенту.")