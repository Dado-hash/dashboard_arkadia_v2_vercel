# Generated by Django 5.0.6 on 2024-07-14 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funds_and_strategies', '0011_transaction_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallet',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
