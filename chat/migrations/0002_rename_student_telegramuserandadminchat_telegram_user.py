# Generated by Django 5.1.4 on 2024-12-21 11:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='telegramuserandadminchat',
            old_name='student',
            new_name='telegram_user',
        ),
    ]
