# Generated by Django 5.1.4 on 2024-12-23 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0009_question_rule'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='answer',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='question',
            name='question',
            field=models.CharField(max_length=562),
        ),
        migrations.AlterField(
            model_name='rule',
            name='rule',
            field=models.TextField(),
        ),
    ]
