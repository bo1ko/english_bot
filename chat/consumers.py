import logging
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from datetime import datetime, timezone

from .models import CustomUser, TelegramUser, TelegramUserAndAdminChat
from .utils import send_async_telegram_message

User = get_user_model()

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.chat_group_name = f"chat_{self.chat_id}"

        await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data["message"]
            user_id = data["user_id"]
            source = data.get("source", "site")
            message_id = data.get("message_id")
            reply_message_id = data.get("reply_message_id", False)
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
                    telegram_text = f"<b><i>Головний адміністратор</i></b>"
                elif user.role == "site_administrator":
                    telegram_text = f"<b><i>Адміністратор {user.first_name}</i></b>"
                elif user.role == "teacher":
                    telegram_text = f"<b><i>Вчитель {user.first_name}</i></b>"
                else:
                    return
                
                if user.role == "site_administrator" or user.role == "super_administrator" and chat.admin_id is None:
                    await self.assign_admin(chat, user)
                    
                telegram_text += f"\n{message}"
                message_id = await send_async_telegram_message(telegram_id, telegram_text, reply_message_id)
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
                    "source": source,
                    "message": new_message["text"],
                    "user_id": user.id,
                    "username": user.username,
                    "timestamp": new_message["created_at"],
                    "message_id": message_id,
                },
            )
        except Exception as e:
            logger.error(e)

    async def chat_message(self, event):
        try:
            source = event["source"]
            message = event["message"]
            user_id = event["user_id"]
            username = event["username"]
            timestamp = event["timestamp"]
            message_id = event.get("message_id")

            await self.send(
                text_data=json.dumps(
                    {
                        "source": source,
                        "message": message,
                        "user_id": user_id,
                        "username": username,
                        "timestamp": timestamp,
                        "message_id": message_id,
                    }
                )
            )
        except Exception as e:
            logger.info(e)
    
    @database_sync_to_async
    def assign_admin(self, chat: TelegramUserAndAdminChat, admin: CustomUser):
        try:
            chat.admin = admin
            chat.save(update_fields=["admin"])
            return True
        except Exception as e:
            logging.error("Assign admin error ", e)
            return False

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
    def create_message(self, chat, user, message, source, message_id=None):
        try:
            new_message = {
                "source": source,
                "sender": user.username,
                "sender_id": user.pk,
                "text": message,
                "message_id": message_id,
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            }

            if chat.messages is None:
                chat.messages = []

            chat.messages.append(new_message)
            chat.save()

            return new_message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None
