from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import ForeignKey


class TelegramUser(models.Model):
    tg_id = models.BigIntegerField(null=False, blank=False)
    username = models.CharField(max_length=264, null=True, blank=True)

    def __str__(self):
        return f"Telegram {self.username if self.username else self.tg_id}"

    class Meta:
        verbose_name = "TelegramUser"
        verbose_name_plural = "TelegramUsers"


class CustomUser(AbstractUser):
    STUDENT = "student"
    TEACHER = "teacher"
    SITE_ADMIN = "site_administrator"
    SUPER_ADMIN = "super_administrator"

    ROLE_CHOICES = [
        (STUDENT, "Student"),
        (TEACHER, "Teacher"),
        (SITE_ADMIN, "Site Administrator"),
        (SUPER_ADMIN, "Super Administrator"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=STUDENT,
    )

    telegram = models.OneToOneField(
        TelegramUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user",
    )

    student_list = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return self.username

    def is_student(self):
        return self.role == self.STUDENT

    def is_teacher(self):
        return self.role == self.TEACHER

    def is_site_administrator(self):
        return self.role == self.SITE_ADMIN

    class Meta:
        verbose_name = "CustomUser"
        verbose_name_plural = "CustomUsers"


class StudentAndTeacherChat(models.Model):
    student = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        limit_choices_to={"role": CustomUser.STUDENT},
        related_name="student_chats",
    )
    teacher = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        limit_choices_to={"role": CustomUser.TEACHER},
        related_name="teacher_chats",
    )
    admin_list = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Chat between student {self.student.username} and teacher {self.teacher.username}"

    class Meta:
        verbose_name = "StudentAndTeacherChat"
        verbose_name_plural = "StudentAndTeacherChats"

class SystemAction(models.Model):
    telegram = ForeignKey("TelegramUser", on_delete=models.DO_NOTHING, null=False, blank=False)
    action = models.JSONField(default=list, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.telegram.username if self.telegram.username else self.telegram.tg_id} {self.action}"

    class Meta:
        verbose_name = "SystemAction"
        verbose_name_plural = "SystemActions"
