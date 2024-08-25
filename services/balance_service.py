from django.utils import timezone
from funds_and_strategies.models import Asset, Balance, Strategy, Fund, ExchangeRate
from django.db.models import Sum
from datetime import date
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BalanceService:
    def calculate_strategy_balance_for_date(self, strategy, balance_date):
        try:
            # Calcola il valore totale in USD
            total_value_usd = Asset.objects.filter(strategy=strategy, date=balance_date).aggregate(total_value=Sum('value_usd'))['total_value'] or 0.0
            
            # Recupera il tasso di cambio per la data specifica
            exchange_rate = ExchangeRate.objects.filter(from_currency='EUR', to_currency='USD', date=balance_date).first()
            
            if exchange_rate:
                total_value_eur = total_value_usd / exchange_rate.rate
            else:
                total_value_eur = None
            
            # Salva il bilancio in USD ed EUR
            balance, created = Balance.objects.update_or_create(
                strategy=strategy,
                date=balance_date,
                defaults={
                    'value_usd': total_value_usd,
                    'value_eur': total_value_eur,
                    'last_updated': timezone.now()
                }
            )
            logger.info(f"Saved balance for {strategy.name} on {balance_date} with value USD {total_value_usd} and EUR {total_value_eur}.")
            return balance
        except Exception as e:
            logger.error(f"Error calculating balance for {strategy.name} on {balance_date}: {e}")

    def calculate_fund_balance_for_date(self, fund, balance_date):
        try:
            strategies = Strategy.objects.filter(fund=fund)
            total_value_usd = Balance.objects.filter(strategy__in=strategies, date=balance_date).aggregate(total_value=Sum('value_usd'))['total_value'] or 0.0
            
            # Recupera il tasso di cambio per la data specifica
            exchange_rate = ExchangeRate.objects.filter(from_currency='EUR', to_currency='USD', date=balance_date).first()
            
            if exchange_rate:
                total_value_eur = total_value_usd / exchange_rate.rate
            else:
                total_value_eur = None  # Puoi decidere come gestire l'assenza di un tasso di cambio
            
            # Salva il bilancio in USD ed EUR
            balance, created = Balance.objects.update_or_create(
                fund=fund,
                date=balance_date,
                defaults={
                    'value_usd': total_value_usd,
                    'value_eur': total_value_eur,
                    'last_updated': timezone.now()
                }
            )
            logger.info(f"Saved balance for {fund.name} on {balance_date} with value USD {total_value_usd} and EUR {total_value_eur}.")
            return balance
        except Exception as e:
            logger.error(f"Error calculating balance for {fund.name} on {balance_date}: {e}")

    def calculate_balances_for_strategy(self, strategy):
        try:
            asset_dates = Asset.objects.filter(strategy=strategy).values_list('date', flat=True).distinct()
            for balance_date in asset_dates:
                self.calculate_strategy_balance_for_date(strategy, balance_date)
        except Exception as e:
            logger.error(f"Error calculating balances for strategy {strategy.name}: {e}")

    def calculate_balances_for_fund(self, fund):
        try:
            balance_dates = Balance.objects.filter(strategy__fund=fund).values_list('date', flat=True).distinct()
            for balance_date in balance_dates:
                self.calculate_fund_balance_for_date(fund, balance_date)
        except Exception as e:
            logger.error(f"Error calculating balances for fund {fund.name}: {e}")

    def update_all_balances(self):
        try:
            Balance.objects.all().delete()
            logger.info("Deleted all existing balances.")

            strategies = Strategy.objects.all()
            for strategy in strategies:
                self.calculate_balances_for_strategy(strategy)
            
            funds = Fund.objects.all()
            for fund in funds:
                self.calculate_balances_for_fund(fund)
        except Exception as e:
            logger.error(f"Error updating all balances: {e}")

# Use this function to trigger the balance update process
def update_all_balances():
    balance_service = BalanceService()
    balance_service.update_all_balances()
