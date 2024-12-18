from django.contrib import admin
from .models import CustomUser, TelegramUser, Chats

admin.site.register([CustomUser, TelegramUser, Chats])
