# Generated by Django 5.0.6 on 2024-07-15 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funds_and_strategies', '0017_alter_balance_value_usd'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='date',
            field=models.DateField(),
        ),
    ]
