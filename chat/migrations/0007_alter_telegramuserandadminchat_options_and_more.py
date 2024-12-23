# Generated by Django 5.1.4 on 2024-12-23 07:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_alter_telegramuserandadminchat_admin_list_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='telegramuserandadminchat',
            options={'verbose_name': 'Telegram User And Admin Chat', 'verbose_name_plural': 'Telegram User And Admin Chats'},
        ),
        migrations.AlterField(
            model_name='telegramuserandadminchat',
            name='admin',
            field=models.ForeignKey(limit_choices_to={'role': 'super_administrator'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admin_student_chats', to=settings.AUTH_USER_MODEL),
        ),
    ]
