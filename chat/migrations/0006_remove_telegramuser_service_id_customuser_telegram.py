# Generated by Django 5.1.4 on 2024-12-18 07:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_remove_chats_admin_list_chats_admin_list'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='telegramuser',
            name='service_id',
        ),
        migrations.AddField(
            model_name='customuser',
            name='telegram',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='chat.telegramuser'),
        ),
    ]
