# Generated by Django 5.0.6 on 2024-07-14 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funds_and_strategies', '0015_balance_modified_by_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='date',
            field=models.DateTimeField(),
        ),
    ]
