from django.contrib import admin
from .models import CustomUser, TelegramUser, StudentAndTeacherChat

admin.site.register([CustomUser, TelegramUser, StudentAndTeacherChat])
