import asyncio
import logging
import os
from typing import Callable, Any, Dict, Awaitable
from asgiref.sync import sync_to_async

from aiogram import Bot, Dispatcher, types, BaseMiddleware
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMedia, BotCommand, TelegramObject
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import django_setup

from chat.models import TelegramUser, SystemAction, CustomUser, Message, StudentAndTeacherChat

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("bot.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

# commands
private = [
    BotCommand(command='start', description='Запустити бота'),
]


@sync_to_async
def get_or_create_user(tg_id: int, username: str) -> TelegramUser:
    return TelegramUser.objects.get_or_create(
        tg_id=tg_id,
        defaults={"username": username if username else None}
    )


@sync_to_async
def get_telegram_user(tg_id: int) -> TelegramUser:
    return TelegramUser.objects.get(tg_id=tg_id)


@sync_to_async
def create_system_action(telegram: TelegramUser, text: str) -> SystemAction:
    try:
        obj, _ = SystemAction.objects.get_or_create(
            telegram=telegram
        )

        if obj.action is None:
            obj.action = []
        obj.action.append(text)
        obj.save()

        return obj
    except Exception as e:
        logger.error(f"Create system action: {e}")


@sync_to_async
def create_message(chat_id: int, sender: TelegramUser, content: str) -> CustomUser:

    try:
        chat = StudentAndTeacherChat.objects.get(id=chat_id)
        user = CustomUser.objects.get(telegram=sender)
        Message.objects.create(chat=chat, sender=user, content=content)

        return user
    except Exception as e:
        logger.error(f"Create message: {e}")


async def send_to_websocket(chat_id: int, user_id: int, message: str):
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f'ws://127.0.0.1:8000/ws/chat/{chat_id}/') as ws:
            await ws.send_json({
                'user_id': user_id,
                'message': message,
            })


class CheckAndAddUserMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        try:
            user, created = await get_or_create_user(event.from_user.id, event.from_user.username)
        except Exception as e:
            print(e)

        return await handler(event, data)


# routers
router = Router()
router.message.middleware(CheckAndAddUserMiddleware())


# handlers
@router.message(CommandStart())
async def cmd_start(message: Message):
    await create_system_action(await get_telegram_user(message.from_user.id), "/start")
    await message.answer("👋")


@router.message(F.text & ~F.command)
async def handle_text_message(message: Message):
    tg_user = await get_telegram_user(message.from_user.id)
    await create_system_action(tg_user, message.text)

    # Отримайте чат між студентом і вчителем
    # Припустимо, у вас є функція для отримання чату
    # chat = StudentAndTeacherChat.objects.get(student=)
    chat_id = 3  # замінить на ваш спосіб визначення чату

    user = await create_message(chat_id, tg_user, message.text)

    # Надсилання повідомлення до WebSocket
    await send_to_websocket(chat_id, user.pk, message.text)

    await message.answer("Ваше повідомлення було надіслано в чат на сайті.")


# start bot func
async def main():
    bot = Bot(
        token=os.getenv("BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_routers(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(
        commands=private, scope=types.BotCommandScopeAllPrivateChats()
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")