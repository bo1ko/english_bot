from django.contrib.auth.models import AbstractUser
from django.db import models


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

    def __str__(self):
        return self.username

    # Можна додати додаткові методи для перевірки ролі
    def is_student(self):
        return self.role == self.STUDENT

    def is_teacher(self):
        return self.role == self.TEACHER

    def is_site_administrator(self):
        return self.role == self.SITE_ADMIN

    class Meta:
        verbose_name = "CustomUser"
        verbose_name_plural = "CustomUsers"


class Chats(models.Model):
    student_id = models.OneToOneField(
        CustomUser,
        on_delete=models.DO_NOTHING,
        null=False,
        blank=False,
        limit_choices_to={"role": CustomUser.STUDENT},
        related_name="student_chats",
    )
    teacher_id = models.OneToOneField(
        CustomUser,
        on_delete=models.DO_NOTHING,
        null=False,
        blank=False,
        limit_choices_to={"role": CustomUser.TEACHER},
        related_name="teacher_chats",
    )
    admin_list = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Chat between student {self.student_id.student_chats.last_name}"

    class Meta:
        verbose_name = "Chat"
        verbose_name_plural = "Chats"
