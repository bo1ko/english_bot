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

from chat.models import TelegramUser, SystemAction

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
