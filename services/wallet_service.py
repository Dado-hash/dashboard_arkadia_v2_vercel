import requests
from datetime import date
from funds_and_strategies.models import Wallet, Asset
from django.utils import timezone
from django.conf import settings

class WalletService:
    ASSET_MAPPING = {
        'bitcoin': 'BTC',
        'ethereum': 'ETH'
    }

    def __init__(self, wallet: Wallet, prices: dict):
        self.wallet = wallet
        self.network = wallet.network.lower()
        self.prices = prices

    def _get_bitcoin_balance(self):
        # Usa l'API pubblica di blockchain.info per ottenere il saldo di un indirizzo Bitcoin
        url = f"https://blockchain.info/rawaddr/{self.wallet.address}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            balance = data['final_balance'] / 1e8  # Converti Satoshi in BTC
            return balance
        else:
            response.raise_for_status()

    def _get_ethereum_balance(self):
        # Usa l'API pubblica di etherscan.io per ottenere il saldo di un indirizzo Ethereum
        api_key = settings.ETHERSCAN_API_KEY
        url = f"https://api.etherscan.io/api?module=account&action=balance&address={self.wallet.address}&tag=latest&apikey={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            balance = int(data['result']) / 1e18  # Converti Wei in ETH
            return balance
        else:
            response.raise_for_status()

    def get_balance(self):
        if self.network == 'bitcoin':
            return self._get_bitcoin_balance()
        elif self.network == 'ethereum':
            return self._get_ethereum_balance()
        else:
            raise ValueError("Unsupported network")

    def save_assets_to_db(self):
        today = date.today()
        balance = self.get_balance()
        asset_name = self.ASSET_MAPPING.get(self.network, self.network.upper())
        price = self.prices.get(f"{asset_name}USDT", 1.0)
        value_usd = balance * price
        
        # Elimina gli asset esistenti per lo stesso giorno
        Asset.objects.filter(strategy=self.wallet.strategy, date=today, wallet=self.wallet).delete()
        
        Asset.objects.create(
            name=asset_name,
            amount=balance,
            price=price,
            value_usd=value_usd,
            strategy=self.wallet.strategy,
            date=today,
            wallet=self.wallet 
        )

        # Aggiorna il campo last_updated
        self.wallet.last_updated = timezone.now()
        self.wallet.save()
