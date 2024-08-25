from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
from django.forms import ValidationError 
from django.utils import timezone

class Fund(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

class Strategy(models.Model):
    name = models.CharField(max_length=255)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    description = models.TextField()
    manual = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Asset(models.Model):
    name = models.CharField(max_length=255)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    exchange_account = models.ForeignKey('ExchangeAccount', null=True, blank=True, on_delete=models.CASCADE)
    wallet = models.ForeignKey('Wallet', null=True, blank=True, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    value_usd = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateField()

    def __str__(self):
        return f"{self.exchange_account.name if self.exchange_account else self.wallet.name} - {self.date}"

    @property
    def exchange_or_wallet(self):
        return self.exchange_account.name if self.exchange_account else self.wallet.name

    class Meta:
        ordering = ['date']

    def clean(self):
        if self.exchange_account and self.wallet:
            raise ValidationError('An asset cannot belong to both an exchange account and a wallet.')

class Balance(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, null=True, blank=True)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True, blank=True)
    value_usd = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    value_eur = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    date = models.DateField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.strategy.name if self.strategy else self.fund.name} - {self.date}"

    @property
    def strategy_or_fund(self):
        return self.strategy.name if self.strategy else self.fund.name

    class Meta:
        ordering = ['date']

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
    ]
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    asset = models.CharField(max_length=255) 
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    value_usd = models.DecimalField(max_digits=20, decimal_places=2)
    value_eur = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateField()
    strategy = models.ForeignKey(Strategy, null=True, blank=True, on_delete=models.SET_NULL)
    fund = models.ForeignKey(Fund, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.strategy.name if self.strategy else self.fund.name} - {self.type} - {self.date}"

    @property
    def strategy_or_fund(self):
        return self.strategy.name if self.strategy else self.fund.name

    class Meta:
        ordering = ['date']

class PerformanceMetric(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, null=True, blank=True)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    metric_name = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=20, decimal_places=2)
    value_eur = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return f"{self.strategy.name if self.strategy else self.fund.name} - {self.metric_name} - {self.date}"

    @property
    def strategy_or_fund(self):
        return self.strategy.name if self.strategy else self.fund.name

    class Meta:
        ordering = ['date']

class ExchangeAccount(models.Model):
    name = models.CharField(max_length=255)
    exchange = models.CharField(max_length=255)
    _api_key = models.BinaryField()
    _api_secret = models.BinaryField()
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(auto_now=True)
    description = models.TextField()

    def _get_cipher(self):
        return Fernet(settings.SECRET_KEY.encode())

    @property
    def api_key(self):
        return self._get_cipher().decrypt(bytes(self._api_key)).decode()

    @api_key.setter
    def api_key(self, value):
        self._api_key = self._get_cipher().encrypt(value.encode())

    @property
    def api_secret(self):
        return self._get_cipher().decrypt(bytes(self._api_secret)).decode()

    @api_secret.setter
    def api_secret(self, value):
        self._api_secret = self._get_cipher().encrypt(value.encode())

    def __str__(self):
        return self.name

class Wallet(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    network = models.CharField(max_length=255)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    description = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class ExchangeRate(models.Model):
    from_currency = models.CharField(max_length=10)
    to_currency = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=20, decimal_places=6)
    date = models.DateField()

    class Meta:
        unique_together = ('from_currency', 'to_currency', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.from_currency}/{self.to_currency} - {self.date}: {self.rate}"

class SavedReport(models.Model):
    name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    currency = models.CharField(max_length=3)  

    def __str__(self):
        return self.name