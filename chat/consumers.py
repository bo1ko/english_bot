import logging
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from datetime import datetime

from .models import TelegramUser, TelegramUserAndAdminChat
from .utils import send_async_telegram_message

User = get_user_model()

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user_id = data['user_id']
        source = data.get('source', 'site')
        chat = await self.get_chat(self.chat_id)
        message_id = None

        if source == 'site':
            user = await self.get_user(user_id)
            telegram_id = await self.get_telegram_user_id(chat)
            message_id = await send_async_telegram_message(telegram_id, f"New message from {user.username}: {message}")
        elif source == 'telegram':
            user = await self.get_telegram_user(user_id)
        else:
            return
        
        new_message = await self.create_message(chat, user, message, message_id)

        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'chat_message',
                'message': new_message['text'],
                'user_id': user.id,
                'username': user.username,
                'timestamp': new_message['created_at']
            }
        )

    async def chat_message(self, event):
        message = event['message']
        user_id = event['user_id']
        username = event['username']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'message': message,
            'user_id': user_id,
            'username': username,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(pk=user_id)
    
    @database_sync_to_async
    def get_telegram_user(self, user_id):
        return TelegramUser.objects.get(pk=user_id)

    @database_sync_to_async
    def get_chat(self, chat_id):
        try:
            chat = TelegramUserAndAdminChat.objects.get(pk=chat_id)
            return chat
        except ObjectDoesNotExist:
            return None
    
    @database_sync_to_async
    def get_telegram_user_id(self, chat):
        return chat.telegram_user.tg_id

    @database_sync_to_async
    def create_message(self, chat, user, message, message_id=None):
        try:
            new_message = {
                "sender": user.username,
                "text": message,
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            if message_id:
                new_message["message_id"] = message_id  # Save message_id if it exists

            if chat.messages is None:
                chat.messages = []

            chat.messages.append(new_message)
            chat.save()

            return new_message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None