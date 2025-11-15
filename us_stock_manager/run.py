import asyncio
from collections import defaultdict

from us_stock_manager.price_monitor import PriceMonitor
from config import StockConfig
from http_handlers.alphavantage_api import AlphaVantageApi


class StockManagerUS:
    def __init__(self, config: StockConfig, us_stock_api: AlphaVantageApi):
        self.us_stock_api = us_stock_api
        self.config = config
        self.cache = {}  # Store last known values
        self.last_fetch = {}  # Track last fetch time per symbol
        self.news_cache = defaultdict(set)  # Track seen news IDs
        self.alert_cooldown = {}  # Prevent duplicate alerts

    async def run(self):
        """Main monitoring loop"""
        price_monitor = PriceMonitor(self.config, self.us_stock_api)
        # Separate tasks for different update frequencies
        tasks = [
            price_monitor.monitor_prices(),  # Fast updates (1-5 min)
            #self.monitor_news(),  # Slower updates (5-15 min)
            #self.check_market_hours(),  # Adjust frequency based on market status
        ]
        await asyncio.gather(*tasks)