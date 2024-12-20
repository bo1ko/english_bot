from django.contrib import admin
from .models import CustomUser, TelegramUser, StudentAndTeacherChat, SystemAction

admin.site.register([CustomUser, TelegramUser, StudentAndTeacherChat, SystemAction])
