# Generated by Django 5.0.6 on 2024-08-22 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funds_and_strategies', '0026_exchangerate'),
    ]

    operations = [
        migrations.AddField(
            model_name='performancemetric',
            name='value_eur',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transaction',
            name='value_eur',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=20),
            preserve_default=False,
        ),
    ]
