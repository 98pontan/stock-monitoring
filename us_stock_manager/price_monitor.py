import asyncio
import logging
import datetime
from typing import List, Dict
from dataclasses import dataclass

from http_handlers.alphavantage_api import AlphaVantageApi

class StockData:
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    previous_close: float


class PriceMonitor:
    def __init__(self, config, us_stock_api: AlphaVantageApi):
        self.config = config
        self.us_stock_api = us_stock_api
        self.previous_closes = {}
        self.previous_close_date = None

    async def monitor_prices(self):
        while True:
            try:
                # 1. Check market status
                active_markets = self.get_active_markets()
                if not active_markets:
                    await asyncio.sleep(300)
                    continue

                # 2. Refresh yesterday close once per day
                await self.ensure_previous_closes()

                # 3. Fetch current prices in smart batches
                companies = self.config.get_companies("us")
                await self.poll_prices_for_companies(companies)

                # 4. Dynamic wait time
                wait_time = self.calculate_wait_time()
                await asyncio.sleep(wait_time)

            except Exception as e:
                logging.error(f"Error in monitor: {e}")
                await asyncio.sleep(60)

    async def ensure_previous_closes(self):
        today = datetime.date.today().isoformat()

        if self.previous_close_date == today:
            return  # already cached today

        companies = self.config.get_companies("us")
        for company in companies:
            symbol = company["symbol"]
            close = self.us_stock_api.get_yesterday_close(symbol)
            self.previous_closes[symbol] = close

        self.previous_close_date = today

    async def poll_prices_for_companies(self, companies):
        for company in companies:
            symbol = company["symbol"]

            current_price = self.us_stock_api.get_current_trading_price(symbol)
            prev_close = self.previous_closes.get(symbol)

            if prev_close is None:
                continue

            percent_change = ((current_price - prev_close) / prev_close) * 100

            print(f"{symbol}: ${current_price} ({percent_change:+.2f}%)")

            # Check configured alert thresholds
            await self.check_alerts(company, current_price, percent_change)

    def get_active_markets(self) -> List[str]:
        """Check which markets are currently open"""
        now = datetime.date.today()
        active = []

        for market_name, market_config in self.config.get_markets().items():
           # if self.is_market_open(market_config, now):
            if market_name == "us":
                active.append(market_name)

        return active

    def calculate_wait_time(self) -> int:
        """Dynamic wait time based on market activity"""
        active_markets = self.get_active_markets()

        if not active_markets:
            return 300  # 5 minutes when closed

        # Check recent volatility
        high_volatility = self.check_volatility()

        if high_volatility:
            return 60  # 1 minute during high volatility
        else:
            return 180  # 3 minutes during normal times
    
    def is_market_open(self, market_config: Dict, time) -> bool:
        """Check if market is currently open"""
        # Implementation depends on your needs
        # Check: weekday, market hours, holidays
        market_hours = market_config['market_hours']['regular']
        # ... implement time checking logic
        return True  # Placeholder