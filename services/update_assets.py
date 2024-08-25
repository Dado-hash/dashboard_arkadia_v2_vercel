from .rates_service import update_exchange_rates_for_all_balances
from .balance_service import update_all_balances
from .metric_service import update_all_performances
from funds_and_strategies.models import ExchangeAccount, Wallet
from .price_service import PriceService
from .exchange_service import ExchangeService
from .wallet_service import WalletService

def update_all_assets():
    # Ottieni i prezzi correnti
    price_service = PriceService()
    prices = price_service.get_prices()

    # Aggiorna gli asset degli account degli exchange
    exchange_accounts = ExchangeAccount.objects.all()
    for account in exchange_accounts:
        exchange_service = ExchangeService(account, prices)
        assets = exchange_service.get_assets()
        exchange_service.save_assets_to_db(assets)

    # Aggiorna gli asset dei wallets
    wallets = Wallet.objects.all()
    for wallet in wallets:
        wallet_service = WalletService(wallet, prices)
        wallet_service.save_assets_to_db()

    # Aggiorna i tassi di cambio per tutti i bilanci
    update_exchange_rates_for_all_balances()

    # Aggiorna i bilanci per tutte le strategie
    update_all_balances()

    # Aggiorna le metriche di performance per tutte le strategie
    update_all_performances()
