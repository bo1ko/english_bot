# Generated by Django 5.1.4 on 2024-12-19 13:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0010_alter_customuser_student_list'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Chats',
            new_name='Chat',
        ),
    ]