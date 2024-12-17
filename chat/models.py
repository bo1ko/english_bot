from django.contrib.auth.models import AbstractUser
from django.db import models


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

    def __str__(self):
        return self.username

    # Можна додати додаткові методи для перевірки ролі
    def is_student(self):
        return self.role == self.STUDENT

    def is_teacher(self):
        return self.role == self.TEACHER

    def is_site_administrator(self):
        return self.role == self.SITE_ADMIN
