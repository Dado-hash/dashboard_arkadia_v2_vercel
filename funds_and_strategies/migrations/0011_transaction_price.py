# Generated by Django 5.0.6 on 2024-07-14 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funds_and_strategies', '0010_wallet'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='price',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=20),
            preserve_default=False,
        ),
    ]
