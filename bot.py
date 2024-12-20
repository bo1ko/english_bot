import asyncio
import django
import os
from typing import Callable, Any, Dict, Awaitable
from asgiref.sync import sync_to_async

from aiogram import Bot, Dispatcher, types, BaseMiddleware
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMedia, BotCommand, TelegramObject
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv


load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()
from chat.models import TelegramUser

# commands
private = [
    BotCommand(command='start', description='Запустити бота'),
]

@sync_to_async
def get_or_create_user(tg_id, username):
    return TelegramUser.objects.get_or_create(
        tg_id=tg_id,
        defaults={"username": username if username else None}
    )

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
