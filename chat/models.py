from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import ForeignKey


class TelegramUser(models.Model):
    tg_id = models.BigIntegerField(null=False, blank=False)
    username = models.CharField(max_length=264, null=True, blank=True)
    first_name = models.CharField(max_length=264, null=True, blank=True)
    last_name = models.CharField(max_length=264, null=True, blank=True)
    phone_number = models.CharField(max_length=264, null=True, blank=True)

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
    student = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        limit_choices_to={"role": CustomUser.STUDENT},
        related_name="student_teacher_chats",
    )
    teacher = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        limit_choices_to={"role": CustomUser.TEACHER},
        related_name="teacher_student_chats",
    )
    admin_list = models.JSONField(blank=True, null=True)
    messages = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"{self.pk} | Chat between student {self.student.username if self.student else None} and teacher {self.teacher.username if self.teacher else None}"

    class Meta:
        verbose_name = "Student And Teacher Chat"
        verbose_name_plural = "Student And Teacher Chats"


class TelegramUserAndAdminChat(models.Model):
    telegram_user = models.OneToOneField(
        TelegramUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="telegram_user_admin_chats",
    )
    admin = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        limit_choices_to={
            "role": CustomUser.SITE_ADMIN,
            "role": CustomUser.SUPER_ADMIN,
        },
        related_name="admin_student_chats",
    )
    admin_list = models.JSONField(default=list, blank=True, null=True)
    messages = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"{self.pk} | Chat between telegram user {self.telegram_user.username} and admin {self.admin.username if self.admin else None}"

    class Meta:
        verbose_name = "Telegram User And Admin Chat"
        verbose_name_plural = "Telegram User And Admin Chats"


class SystemAction(models.Model):
    telegram = ForeignKey("TelegramUser",
                          on_delete=models.DO_NOTHING,
                          null=False,
                          blank=False)
    action = models.JSONField(default=list, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.telegram.username if self.telegram.username else self.telegram.tg_id} {self.action}"

    class Meta:
        verbose_name = "System Action"
        verbose_name_plural = "System Actions"


class Question(models.Model):
    question = models.CharField(max_length=562, null=False, blank=False)
    answer = models.TextField(null=False, blank=False)

    def __str__(self):
        return f"{self.question} | {self.answer}"

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"


class Rule(models.Model):
    rule = models.TextField(null=False, blank=False)

    def __str__(self):
        return f"{self.rule}"

    class Meta:
        verbose_name = "Rule"
        verbose_name_plural = "Rules"


class Course(models.Model):
    name = models.CharField(max_length=562, null=False, blank=True)
    description = models.TextField(null=False, blank=False)
    image_url = models.ImageField(upload_to="images/", null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"


class TeacherAndAdminChat(models.Model):
    admin = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        limit_choices_to={
            "role": CustomUser.SITE_ADMIN,
            "role": CustomUser.SUPER_ADMIN,
        },
        related_name="admin_teacher_chats",
    )
    teacher = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        limit_choices_to={"role": CustomUser.TEACHER},
        related_name="teacher_admin_chats",
    )
    admin_list = models.JSONField(blank=True, null=True)
    messages = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"{self.pk} | Chat between teacher {self.teacher.username} and admin {self.admin.username}"

    class Meta:
        verbose_name = "Teacher And Admin Chat"
        verbose_name_plural = "Teacher And Admin Chats"
