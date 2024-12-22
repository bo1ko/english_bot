from django.contrib import admin
from .models import CustomUser, TelegramUser, StudentAndTeacherChat, TelegramUserAndAdminChat, SystemAction

admin.site.register([CustomUser, TelegramUser, StudentAndTeacherChat, TelegramUserAndAdminChat, SystemAction])
