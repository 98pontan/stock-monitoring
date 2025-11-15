import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Set
import logging
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class StockData:
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    previous_close: float


@dataclass
class NewsItem:
    symbol: str
    title: str
    source: str
    published: datetime
    url: str


class StockMonitor:
    def __init__(self, config: Dict, ):
        self.config = config
        self.cache = {}  # Store last known values
        self.last_fetch = {}  # Track last fetch time per symbol
        self.news_cache = defaultdict(set)  # Track seen news IDs
        self.alert_cooldown = {}  # Prevent duplicate alerts



    

    async def fetch_batch_prices(self, symbols: List[str], market: str) -> Dict:
        """Fetch multiple stocks in one API call"""
        # Most APIs support batch requests like:
        # API: ?symbols=AAPL,GOOGL,MSFT

        batch_size = 100  # Adjust based on API limits
        results = {}

        async with aiohttp.ClientSession() as session:
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                symbols_str = ','.join(batch)

                # Example API call (adjust to your provider)
                url = f"https://api.example.com/batch?symbols={symbols_str}"

                async with session.get(url) as response:
                    data = await response.json()
                    results.update(data)

        return results

    async def process_price_updates(self, stock_data: Dict, market: str):
        """Check thresholds and send alerts efficiently"""
        alerts_to_send = []

        for symbol, data in stock_data.items():
            # Get company config
            company = self.config.get_company_config(symbol)
            if not company or not company['price_alerts']['enabled']:
                continue

            # Compare with cached value
            cached = self.cache.get(symbol)
            if not cached:
                # First fetch - just cache it
                self.cache[symbol] = data
                continue

            # Calculate change
            change_percent = ((data['price'] - cached['previous_close']) /
                              cached['previous_close'] * 100)

            # Check threshold
            threshold = company['price_alerts']['conditions'][0]['threshold_percent']
            if abs(change_percent) >= threshold:
                # Check cooldown to prevent spam
                if self.should_send_alert(symbol, 'price'):
                    alerts_to_send.append({
                        'type': 'price',
                        'symbol': symbol,
                        'company': company,
                        'data': data,
                        'change': change_percent
                    })
                    self.set_alert_cooldown(symbol, 'price')

            # Update cache
            self.cache[symbol] = data

        # Batch send alerts
        if alerts_to_send:
            await self.send_alerts_batch(alerts_to_send)

    async def monitor_news(self):
        """Monitor news with less frequent updates"""
        while True:
            try:
                # Group companies by news sources to minimize API calls
                source_groups = self.group_by_news_sources()

                for source, companies in source_groups.items():
                    symbols = [c['symbol'] for c in companies]

                    # Fetch news for multiple symbols at once
                    news_items = await self.fetch_news_batch(symbols, source)

                    # Filter and process
                    await self.process_news_updates(news_items, companies)

                # News updates less frequently (5-15 minutes)
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logging.error(f"Error in news monitoring: {e}")
                await asyncio.sleep(300)

    async def fetch_news_batch(self, symbols: List[str], source: str) -> List[NewsItem]:
        """Fetch news for multiple companies in one call"""
        # Most news APIs support querying multiple symbols
        # Example: ?q=(AAPL OR GOOGL OR MSFT)

        query = ' OR '.join(symbols)
        url = f"https://newsapi.org/v2/everything?q={query}&apiKey=YOUR_KEY"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                return self.parse_news_response(data)

    def group_by_news_sources(self) -> Dict[str, List]:
        """Group companies by their news sources to batch requests"""
        groups = defaultdict(list)

        for market in ['swedish', 'us']:
            companies = self.config['companies'][market]
            for company in companies:
                if company['news_alerts']['enabled']:
                    sources = company['news_alerts']['sources']
                    for source in sources:
                        groups[source].append(company)

        return groups

    def get_active_markets(self) -> List[str]:
        """Check which markets are currently open"""
        now = datetime.now()
        active = []

        for market_name, market_config in self.config['markets'].items():
            if self.is_market_open(market_config, now):
                active.append(market_name)

        return active

    def is_market_open(self, market_config: Dict, time: datetime) -> bool:
        """Check if market is currently open"""
        # Implementation depends on your needs
        # Check: weekday, market hours, holidays
        market_hours = market_config['market_hours']['regular']
        # ... implement time checking logic
        return True  # Placeholder

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

    def should_send_alert(self, symbol: str, alert_type: str) -> bool:
        """Check if enough time has passed since last alert"""
        key = f"{symbol}:{alert_type}"
        last_alert = self.alert_cooldown.get(key)

        if not last_alert:
            return True

        # Cooldown period: 15 minutes for price, 30 minutes for news
        cooldown = 900 if alert_type == 'price' else 1800

        return (datetime.now() - last_alert).seconds > cooldown

    def set_alert_cooldown(self, symbol: str, alert_type: str):
        """Set cooldown timer for alerts"""
        key = f"{symbol}:{alert_type}"
        self.alert_cooldown[key] = datetime.now()

    async def send_alerts_batch(self, alerts: List[Dict]):
        """Send multiple alerts efficiently"""
        # Group alerts by notification channel
        email_alerts = []
        slack_alerts = []

        for alert in alerts:
            # Format the alert
            formatted = self.format_alert(alert)

            if 'email' in self.config['notifications']['channels']:
                email_alerts.append(formatted)
            if 'slack' in self.config['notifications']['channels']:
                slack_alerts.append(formatted)

        # Send in batches
        tasks = []
        if email_alerts:
            tasks.append(self.send_email_batch(email_alerts))
        if slack_alerts:
            tasks.append(self.send_slack_batch(slack_alerts))

        await asyncio.gather(*tasks)

    def check_volatility(self) -> bool:
        """Check if market is experiencing high volatility"""
        # Analyze recent price movements
        # Return True if many stocks are moving significantly
        return False  # Placeholder


# Usage
async def main():
    import yaml

    with open('stock_config.yaml') as f:
        config = yaml.safe_load(f)

    monitor = StockMonitor(config)
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())