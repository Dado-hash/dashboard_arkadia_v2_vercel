# forms.py
from django import forms
from .models import Asset, ExchangeAccount, Fund, Strategy, Transaction, Wallet
from django.forms import modelformset_factory

class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ['name', 'description']

class StrategyForm(forms.ModelForm):
    class Meta:
        model = Strategy
        fields = ['name', 'fund', 'manual', 'description']

class ExchangeAccountForm(forms.ModelForm):
    EXCHANGE_CHOICES = [
        ('binance', 'Binance'),
        ('binance_futures', 'Binance Futures'),
        ('deribit', 'Deribit'),
        ('kraken', 'Kraken'),
    ]
    
    exchange = forms.ChoiceField(choices=EXCHANGE_CHOICES)

    api_key = forms.CharField(widget=forms.TextInput, label="API Key")
    api_secret = forms.CharField(widget=forms.PasswordInput, label="API Secret")

    class Meta:
        model = ExchangeAccount
        fields = ['name', 'exchange', 'strategy', 'description']

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.api_key = self.cleaned_data['api_key']
        instance.api_secret = self.cleaned_data['api_secret']
        if commit:
            instance.save()
        return instance
    
class WalletForm(forms.ModelForm):
    NETWORK_CHOICES = [
        ('bitcoin', 'Bitcoin'),
        ('ethereum', 'Ethereum'),
    ]

    name = forms.CharField(widget=forms.TextInput, label="Wallet Name")

    address = forms.CharField(widget=forms.TextInput, label="Address")
    network = forms.ChoiceField(choices=NETWORK_CHOICES, label="Network")

    class Meta:
        model = Wallet
        fields = ['name', 'strategy', 'address', 'network', 'description']

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'strategy', 'exchange_account','amount', 'price', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

AssetFormSet = modelformset_factory(Asset, form=AssetForm, extra=1)

class TransactionForm(forms.ModelForm):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
    ]

    type = forms.ChoiceField(choices=TRANSACTION_TYPES)

    class Meta:
        model = Transaction
        fields = ['type', 'asset', 'amount', 'price', 'date', 'strategy', 'fund']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

TransactionFormSet = modelformset_factory(Transaction, form=TransactionForm, extra=1)