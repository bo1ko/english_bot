# Generated by Django 5.1.4 on 2024-12-19 13:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0012_rename_student_id_chat_student_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Chat',
            new_name='StudentAndTeacherChat',
        ),
    ]