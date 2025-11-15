from typing import List, Dict

import datetime
import requests
import requests.sessions

api_key = "CKU1OG056UPM3KTD"

class AlphaVantageSession(requests.Session):
    def __init__(self):
        super().__init__()
        self.params = {"apikey": api_key}
        self.headers.update({"Content-Type": "application/json"})


class AlphaVantageApi:
    def __init__(self):
        self.session = AlphaVantageSession()


    #def get_companies(self, market: str = None) -> List[Dict]:

    def get_current_trading_price(self, symbol: str) -> float:
        params = {"apikey": api_key,
                  "function": "TIME_SERIES_INTRADAY",
                  "symbol": symbol,
                  "interval": "1min"
                  }

        response = self.session.get("https://www.alphavantage.co/query", params=params)
        response.raise_for_status()
        response_json = response.json()

        print(response_json)
        time_series = response_json.get("Time Series (1min)")

        for _, value  in time_series.items():
            return float(value["4. close"])


    def get_yesterday_close(self, symbol: str) -> float:
        params = {"apikey": api_key,
                  "function": "TIME_SERIES_DAILY",
                  "symbol": symbol,
                  "interval": "1min"
                  }

        response = self.session.get("https://www.alphavantage.co/query", params=params)
        response.raise_for_status()

        response_json = response.json()
        print(response_json)
        time_series = response_json.get("Time Series (Daily)")

        yesterday = get_yesterday()

        for key, value in time_series.items():
            if key == yesterday:
                return float(value["4. close"])

    def send_request(self, url: str, params: dict = None) -> Dict:
        with self.session.get(url, params=params) as response:
            response.raise_for_status()

            return response.json()

def get_yesterday() -> str:
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    year = yesterday.year
    month = yesterday.month
    day = yesterday.day
    formatted_yesterday = f"{year}-{month}-{day}"
    return formatted_yesterday

