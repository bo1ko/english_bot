import logging
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from datetime import datetime, timezone

from .models import TelegramUser, TelegramUserAndAdminChat
from .utils import send_async_telegram_message

User = get_user_model()

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.chat_group_name = f"chat_{self.chat_id}"

        # Join chat group
        await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave chat group
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        user_id = data["user_id"]
        source = data.get("source", "site")
        message_id = data.get("message_id")
        chat = await self.get_chat(self.chat_id)

        if not chat:
            logger.error(f"Chat with ID {self.chat_id} not found")
            return

        if source == "site":
            user = await self.get_user(user_id)
            if not user:
                logger.error(f"User with ID {user_id} not found")
                return

            telegram_id = await self.get_telegram_user_id(chat)
            if not telegram_id:
                logger.error(f"Telegram user ID not found for chat {self.chat_id}")
                return

            if user.role == "super_administrator":
                telegram_text = f"<blockquote>Головний адміністратор</blockquote>"
            elif user.role == "site_administrator":
                telegram_text = f"<blockquote>Адміністратор {user.first_name}</blockquote>"
            elif user.role == "teacher":
                telegram_text = f"<blockquote>Вчитель {user.first_name}</blockquote>"
            else:
                return

            telegram_text += f"\n\n{message}"
            message_id = await send_async_telegram_message(telegram_id, telegram_text)
        elif source == "telegram":
            user = await self.get_telegram_user(user_id)
            if not user:
                logger.error(f"Telegram user with ID {user_id} not found")
                return
        else:
            return

        new_message = await self.create_message(chat, user, message, source=source, message_id=message_id)
        if not new_message:
            logger.error("Failed to create new message")
            return

        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                "type": "chat_message",
                "message": new_message["text"],
                "user_id": user.id,
                "username": user.username,
                "timestamp": new_message["created_at"],
                "message_id": message_id,
            },
        )

    async def chat_message(self, event):
        message = event["message"]
        user_id = event["user_id"]
        username = event["username"]
        timestamp = event["timestamp"]
        message_id = event.get("message_id")

        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "user_id": user_id,
                    "username": username,
                    "timestamp": timestamp,
                    "message_id": message_id,
                }
            )
        )

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_telegram_user(self, user_id):
        try:
            return TelegramUser.objects.get(pk=user_id)
        except TelegramUser.DoesNotExist:
            return None

    @database_sync_to_async
    def get_chat(self, chat_id):
        try:
            return TelegramUserAndAdminChat.objects.get(pk=chat_id)
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def get_telegram_user_id(self, chat):
        try:
            return chat.telegram_user.tg_id
        except AttributeError:
            return None

    @database_sync_to_async
    def create_message(self, chat, user, message, source="site", message_id=None):
        try:
            new_message = {
                "sender": user.username,
                "text": message,
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            }

            if source == "telegram":
                new_message["tg_user_message_id"] = message_id

            if message_id and source == "site":
                new_message["message_id"] = message_id

            if chat.messages is None:
                chat.messages = []

            chat.messages.append(new_message)
            chat.save()

            return new_message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None