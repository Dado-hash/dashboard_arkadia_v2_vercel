import yfinance as yf
from datetime import date, datetime, timedelta
from funds_and_strategies.models import ExchangeRate, Balance

def fetch_and_save_exchange_rates(from_currency, to_currency, start_date, end_date):
    pair = f"{from_currency}{to_currency}=X"
    
    # Fetch the historical data
    data = yf.download(pair, start=start_date, end=end_date)

    if data.empty:
        raise ValueError(f"No data fetched for {pair} between {start_date} and {end_date}.")

    rates_to_save = []

    for idx, row in data.iterrows():
        date_str = idx.date()
        rate = row['Close']

        # Controlla se il tasso di cambio esiste già nel database
        if not ExchangeRate.objects.filter(from_currency=from_currency, to_currency=to_currency, date=date_str).exists():
            rates_to_save.append(
                ExchangeRate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=rate,
                    date=date_str
                )
            )

    # Salva tutti i tassi di cambio in una singola operazione per migliorare le prestazioni
    ExchangeRate.objects.bulk_create(rates_to_save)

    # Ottieni il tasso di cambio corrente
    ticker = yf.Ticker(pair)
    todays_data = ticker.history(period="1d")
    if not todays_data.empty:
        latest_rate = todays_data['Close'].iloc[-1]
        today_date = date.today()

        if not ExchangeRate.objects.filter(from_currency=from_currency, to_currency=to_currency, date=today_date).exists():
            ExchangeRate.objects.create(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=latest_rate,
                date=today_date
            )

    # Replica i tassi di cambio del venerdì per il sabato e la domenica
    last_saved_rate = None
    for single_date in daterange(start_date, end_date):
        if single_date.weekday() in [5, 6]:  # Sabato o Domenica
            friday_date = single_date - timedelta(days=(single_date.weekday() - 4))  # Trova il venerdì precedente
            friday_rate = ExchangeRate.objects.filter(from_currency=from_currency, to_currency=to_currency, date=friday_date).first()
            if friday_rate and not ExchangeRate.objects.filter(from_currency=from_currency, to_currency=to_currency, date=single_date).exists():
                rates_to_save.append(
                    ExchangeRate(
                        from_currency=from_currency,
                        to_currency=to_currency,
                        rate=friday_rate.rate,
                        date=single_date
                    )
                )
            last_saved_rate = friday_rate.rate if friday_rate else last_saved_rate

    # Salva le repliche dei tassi di cambio in una singola operazione
    ExchangeRate.objects.bulk_create(rates_to_save)

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def update_exchange_rates_for_all_balances():
    oldest_balance = Balance.objects.earliest('date')
    start_date = oldest_balance.date
    end_date = date.today()

    # Specifica le valute da scaricare
    from_currency = 'EUR'
    to_currency = 'USD'

    fetch_and_save_exchange_rates(from_currency, to_currency, start_date, end_date)
