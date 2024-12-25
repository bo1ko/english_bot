from django.contrib import admin
from .models import (
    CustomUser,
    TelegramUser,
    StudentAndTeacherChat,
    TelegramUserAndAdminChat,
    SystemAction,
    Rule,
    Question,
    Course,
    TeacherAndAdminChat
)

admin.site.register(
    [
        CustomUser,
        TelegramUser,
        StudentAndTeacherChat,
        TelegramUserAndAdminChat,
        SystemAction,
        Rule,
        Question,
        Course,
        TeacherAndAdminChat
    ]
)
