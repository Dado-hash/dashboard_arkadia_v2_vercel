import requests

class PriceService:
    def __init__(self):
        self.base_url_binance = "https://api.binance.com"
        self.prices = {}

    def _get_binance_prices(self):
        endpoint = "/api/v3/ticker/price"
        url = f"{self.base_url_binance}{endpoint}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            self.prices = {item['symbol']: float(item['price']) for item in data}
        else:
            response.raise_for_status()

    def get_prices(self):
        self._get_binance_prices()
        return self.prices