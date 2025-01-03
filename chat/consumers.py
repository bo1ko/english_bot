import os
import base64
import logging
import json
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import datetime, timezone

from .models import (
    CustomUser,
    TeacherAndAdminChat,
    TelegramUser,
    TelegramUserAndAdminChat,
    StudentAndTeacherChat,
)
from .utils import send_async_alert_message, send_async_telegram_message, send_telegram_media

User = get_user_model()

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.chat_group_name = f"chat_{self.chat_id}"

        await self.channel_layer.group_add(self.chat_group_name,
                                           self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.chat_group_name,
                                               self.channel_name)

    async def receive(self, text_data):
        try:
            logger.info("Received data: %s", text_data)
            data = json.loads(text_data)
            message = data.get("message")
            user_id = data["user_id"]
            source = data.get("source", "site")
            message_id = data.get("message_id")
            reply_message_id = data.get("reply_message_id", False)
            chat_with = data.get("chat_with")
            files = data.get("files", [])  # List of files
            file_type = data.get("file_type")
            file_urls = []

            chat = await self.get_chat(self.chat_id, chat_with)

            if not chat:
                logger.error(f"Chat with ID {self.chat_id} not found")
                return

            # if message sent from website
            if source == "site":
                user = await self.get_user(int(user_id))
                if not user:
                    logger.error(f"User with ID {user_id} not found")
                    return

                if chat_with != "teacher":
                    telegram_id = await self.get_telegram_user_id(
                        chat, chat_with)

                    if not telegram_id:
                        logger.error(
                            f"Telegram user ID not found for chat {self.chat_id}"
                        )
                        return

                if user.role == "super_administrator":
                    telegram_text = f"<b><i>Головний адміністратор</i></b>"
                elif user.role == "site_administrator":
                    telegram_text = f"<b><i>Адміністратор {user.first_name}</i></b>"
                elif user.role == "teacher":
                    telegram_text = f"<b><i>Вчитель {user.first_name}</i></b>"
                else:
                    logger.error("user.role exit")
                    return

                if chat_with == "telegram_user":
                    if (user.role == "site_administrator"
                            or user.role == "super_administrator"
                            and await self.is_admin_none(chat)):
                        await self.assign_admin(chat, user)
                elif chat_with == "student":
                    if (user.role == "site_administrator"
                            or user.role == "super_administrator"
                            or user.role == "teacher"
                            and await self.is_teacher_none(chat)):
                        await self.assign_teacher(chat, user)
                elif chat_with == "teacher":
                    pass
                else:
                    logger.error("chat_with exit")
                    return

                if chat_with != "teacher":
                    if message:
                        telegram_text += f"\n{message}"

                    #     for file_url in file_urls:
                    #         message_id = await send_async_telegram_media(
                    #             telegram_id, file_url, reply_message_id)

                    if not files:
                        message_id = await send_async_telegram_message(
                            telegram_id, telegram_text, reply_message_id)

            # if message sent from telegram
            elif source == "telegram":

                user = await self.get_telegram_user(user_id)

                if not user:
                    logger.error(f"Telegram user with ID {user_id} not found")
                    return
            else:
                return

            if files:
                for file in files:
                    file_data = file["data"]
                    file_name = file["name"]
                    file_path = self.save_file(file_data, file_name)
                    if file_path:
                        file_urls.append(file_path)

            # set whom to send a notification about a new message on the website
            send_to = await self.get_data_for_alert(chat, user)
            if send_to:
                await send_async_alert_message(*send_to)

            # make message body
            new_message = await self.create_message(
                chat,
                user,
                message,
                source=source,
                message_id=message_id,
                files=file_urls,
                file_type=file_type,
            )
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
                    "file_urls": new_message.get("file_urls", []),
                },
            )
        except Exception as e:
            print(e)
            logger.error("Receive error", exc_info=True)

    async def chat_message(self, event):
        try:
            source = event["source"]
            message = event["message"]
            user_id = event["user_id"]
            username = event["username"]
            timestamp = event["timestamp"]
            message_id = event.get("message_id")
            file_urls = event.get("file_urls", [])

            await self.send(text_data=json.dumps({
                "source": source,
                "message": message,
                "user_id": user_id,
                "username": username,
                "timestamp": timestamp,
                "message_id": message_id,
                "file_urls": file_urls,
            }))
        except Exception as e:
            logger.info(e)

    @database_sync_to_async
    def is_admin_none(self, chat: TelegramUserAndAdminChat):
        return chat.admin is None

    @database_sync_to_async
    def is_teacher_none(self, chat: StudentAndTeacherChat):
        return chat.teacher is None

    @database_sync_to_async
    def assign_admin(self, chat: TelegramUserAndAdminChat, admin: CustomUser):
        try:
            chat.admin = admin
            chat.save(update_fields=["admin"])
            return True
        except Exception as e:
            logging.error("Assign admin error", e)
            return False

    @database_sync_to_async
    def assign_teacher(self, chat: StudentAndTeacherChat, teacher: CustomUser):
        try:
            chat.teacher = teacher
            chat.save(update_fields=["teacher"])
            return True
        except Exception as e:
            logging.error("Assign teacher error", e)
            return False

    @database_sync_to_async
    def get_user(self, user_id: int):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_telegram_user(self, user_id):
        try:
            return TelegramUser.objects.get(pk=user_id)
        except Exception as e:
            logging.error("get_telegram_user error", e)
            return None

    @database_sync_to_async
    def get_chat(self, chat_id, chat_with):
        try:
            if chat_with == "telegram_user":
                return TelegramUserAndAdminChat.objects.get(pk=chat_id)
            elif chat_with == "student":
                return StudentAndTeacherChat.objects.get(pk=chat_id)
            elif chat_with == "teacher":
                return TeacherAndAdminChat.objects.get(pk=chat_id)
            else:
                print('Exit')
                return
        except Exception as e:
            logger.error("get_chat error", e)
            return None

    @database_sync_to_async
    def create_message(
        self,
        chat,
        user,
        message,
        source,
        message_id=None,
        files=None,
        file_type=None,
    ):
        try:
            new_message = {
                "source":
                source,
                "sender":
                user.username,
                "sender_id":
                user.pk,
                "text":
                message,
                "message_id":
                message_id,
                "created_at":
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            }

            if files:
                new_message["file_urls"] = files
                new_message["file_type"] = file_type

            if chat.messages is None:
                chat.messages = []

            chat.messages.append(new_message)
            chat.save()

            return new_message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None

    def save_file(self, file_data, file_name):
        try:
            file_extension = file_name.split('.')[-1]
            unique_name = f"{uuid.uuid4()}.{file_extension}"

            if file_extension.lower() in ['jpg', 'jpeg', 'png', 'gif']:
                directory = 'images'
            elif file_extension.lower() in ['mp4', 'avi', 'mov']:
                directory = 'videos'
            elif file_extension.lower() in ['wav', 'mp3', 'aac', 'ogg']:
                directory = 'audios'
            else:
                directory = 'others'

            file_path = os.path.join(settings.MEDIA_ROOT, directory,
                                     unique_name)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as file:
                file.write(base64.b64decode(file_data))

            return os.path.join(settings.MEDIA_URL, directory, unique_name)
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return None

    @database_sync_to_async
    def get_data_for_alert(self, chat, user):
        if type(chat) == TelegramUserAndAdminChat:
            if type(user) == TelegramUser and chat.admin.telegram is not None:
                return (chat.admin.telegram.tg_id, "телеграм користувача",
                        chat.telegram_user.first_name)
        elif type(chat) == StudentAndTeacherChat:
            if type(
                    user
            ) == TelegramUser and chat.student.role == "student" and chat.teacher.telegram is not None:
                return (chat.teacher.telegram.tg_id, "студента",
                        user.first_name)
        elif type(chat) == TeacherAndAdminChat:
            if type(user) == CustomUser:
                if user.username == chat.admin.username and chat.teacher.telegram is not None:
                    return (chat.teacher.telegram.tg_id, "адміністратора",
                            user.first_name)
                elif user.username == chat.teacher.username and chat.admin.telegram is not None:
                    return (chat.admin.telegram.tg_id, "вчителя",
                            user.first_name)

    @database_sync_to_async
    def get_telegram_user_id(self, chat, chat_with):
        try:
            if chat_with == "telegram_user":
                return chat.telegram_user.tg_id
            elif chat_with == "student":
                if chat.student.telegram:
                    return chat.student.telegram.tg_id
                else:
                    return
        except Exception as e:
            logger.error("get_telegram_user_id error", e)
            return None
