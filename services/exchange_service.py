# services/exchange_service.py

import ccxt
from datetime import date
from funds_and_strategies.models import ExchangeAccount, Asset
from django.utils import timezone
import time

class ExchangeService:
    KRAKEN_ASSET_MAPPING = {
        'ZEUR': 'EUR',
        'XXBT': 'BTC',
        'XETH': 'ETH',
        'USDT.F': 'USDT',
        'USDC.F': 'USDC',
        'XBT.F': 'BTC',
    }

    def __init__(self, exchange_account: ExchangeAccount, prices: dict):
        self.api_key = exchange_account.api_key
        self.api_secret = exchange_account.api_secret
        self.exchange = exchange_account.exchange.lower()
        self.prices = prices
        self.exchange_account = exchange_account
        
        if self.exchange == 'binance':
            self.client = ccxt.binance({
                'apiKey': self.api_key,
                'secret': self.api_secret,
            })
        elif self.exchange == 'binance_futures':
            self.client = ccxt.binanceusdm({
                'apiKey': self.api_key,
                'secret': self.api_secret,
            })
        elif self.exchange == 'kraken':
            self.client = ccxt.kraken({
                'apiKey': self.api_key,
                'secret': self.api_secret,
            })
            self.client.nonce = lambda: str(int(time.time() * 1e6))  # Set nonce to microseconds
        elif self.exchange == 'deribit':
            self.client = ccxt.deribit({
                'apiKey': self.api_key,
                'secret': self.api_secret,
            })
        else:
            raise ValueError("Unsupported exchange")

    def get_assets(self):
        if self.exchange == 'binance' or self.exchange == 'binance_futures':
            return self._get_binance_assets()
        elif self.exchange == 'kraken':
            return self._get_kraken_assets()
        elif self.exchange == 'deribit':
            return self._get_deribit_assets()
        else:
            raise ValueError("Unsupported exchange")

    def _get_binance_assets(self):
        balances = self.client.fetch_balance()
        assets = [
            {
                "name": asset,
                "amount": balances['total'][asset],
                "price": self.prices.get(f"{asset}USDT", 1.0),
                "value_usd": balances['total'][asset] * self.prices.get(f"{asset}USDT", 1.0),
                "date": date.today()
            }
            for asset in balances['total']
            if balances['total'][asset] > 0
        ]
        return assets

    def _get_kraken_assets(self):
        balances = self.client.fetch_balance()
        assets = [
            {
                "name": self.KRAKEN_ASSET_MAPPING.get(asset, asset),
                "amount": balances['total'][asset],
                "price": self.prices.get(f"{self.KRAKEN_ASSET_MAPPING.get(asset, asset)}USDT", 1.0),
                "value_usd": balances['total'][asset] * self.prices.get(f"{self.KRAKEN_ASSET_MAPPING.get(asset, asset)}USDT", 1.0),
                "date": date.today()
            }
            for asset in balances['total']
            if balances['total'][asset] > 0
        ]
        return assets

    def _get_deribit_assets(self):
        assets = []
        for currency in ['BTC', 'ETH', "SOL", "USDC"]:
            balance = self.client.fetch_balance({'currency': currency})
            asset = {
                "name": currency,
                "amount": balance['total'][currency],
                "price": self.prices.get(f"{currency}USDT", 1.0),
                "value_usd": balance['total'][currency] * self.prices.get(f"{currency}USDT", 1.0),
                "date": date.today()
            }
            assets.append(asset)
        return assets

    def save_assets_to_db(self, assets):
        today = date.today()
        # Elimina gli asset esistenti per lo stesso giorno
        Asset.objects.filter(strategy=self.exchange_account.strategy, date=today, exchange_account=self.exchange_account).delete()
        for asset in assets:
            if asset['value_usd'] > 0:
                Asset.objects.create(
                    name=asset['name'],
                    amount=asset['amount'],
                    price=asset['price'],
                    value_usd=asset['value_usd'],
                    strategy=self.exchange_account.strategy,
                    date=today,
                    exchange_account=self.exchange_account
                )
        # Aggiorna il campo last_updated
        self.exchange_account.last_updated = timezone.now()
        self.exchange_account.save()
