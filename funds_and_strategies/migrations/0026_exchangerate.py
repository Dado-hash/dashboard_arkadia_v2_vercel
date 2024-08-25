# Generated by Django 5.0.6 on 2024-08-22 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funds_and_strategies', '0025_transaction_fund'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExchangeRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_currency', models.CharField(max_length=10)),
                ('to_currency', models.CharField(max_length=10)),
                ('rate', models.DecimalField(decimal_places=6, max_digits=20)),
                ('date', models.DateField()),
            ],
            options={
                'ordering': ['date'],
                'unique_together': {('from_currency', 'to_currency', 'date')},
            },
        ),
    ]
