import yaml
from pathlib import Path
from typing import Dict, List, Any


class StockConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Load and parse the stock monitoring configuration YAML file.

        Returns:
            Dictionary containing the parsed configuration
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)

        except FileNotFoundError:
            print(f"Error: Configuration file '{self.config_path}' not found!")

        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")

        except Exception as e:
            print(f"Error: {e}")

        return config


    def get_global_settings(self) -> Dict:
        """Extract global settings from config."""
        return self.config.get('global', {})


    def get_notification_settings(self) -> Dict:
        """Extract notification settings from config."""
        return self.config.get('notifications', {})


    def get_markets(self) -> Dict:
        """Extract markets configuration from config."""
        return self.config.get('markets', {})


    def get_companies(self, market: str = None) -> List[Dict]:
        """
        Extract companies from config.

        Args:
            config: The configuration dictionary
            market: Optional market filter ('swedish' or 'us')

        Returns:
            List of company dictionaries
        """
        companies = self.config.get('companies', {})

        if market:
            return companies.get(market, [])

        # Return all companies from all markets
        all_companies = []
        for market_name, company_list in companies.items():
            for company in company_list:
                company['market'] = market_name  # Add market info to each company
                all_companies.append(company)

        return all_companies


    def get_alert_format(self) -> Dict:
        """Extract alert format templates from config."""
        return self.config.get('alert_format', {})


    def get_logging_settings(self) -> Dict:
        """Extract logging settings from config."""
        return self.config.get('logging', {})


    def print_config_summary(self):
        """Print a summary of the loaded configuration."""
        print("=" * 60)
        print("Configuration Summary")
        print("=" * 60)

        # Global settings
        global_settings = self.get_global_settings()
        print(f"\n📊 Global Settings:")
        print(f"  Update Interval: {global_settings.get('update_interval')}s")
        print(f"  Timezone: {global_settings.get('timezone')}")

        # Markets
        markets = self.get_markets()
        print(f"\n🌍 Markets Configured: {len(markets)}")
        for market_name, market_info in markets.items():
            print(f"  - {market_name.upper()}: {market_info.get('exchange')} ({market_info.get('currency')})")

        # Companies
        companies = self.config.get('companies', {})
        print(f"\n🏢 Companies Monitored:")
        for market_name, company_list in companies.items():
            print(f"  {market_name.upper()}: {len(company_list)} companies")
            for company in company_list:
                price_enabled = company.get('price_alerts', {}).get('enabled', False)
                news_enabled = company.get('news_alerts', {}).get('enabled', False)
                alerts = []
                if price_enabled:
                    alerts.append('Price')
                if news_enabled:
                    alerts.append('News')
                print(f"    • {company['symbol']} - {company['name']} [{', '.join(alerts)}]")

        # Notifications
        notifications = self.get_notification_settings()
        if notifications.get('enabled'):
            channels = notifications.get('channels', [])
            print(f"\n📬 Notification Channels: {', '.join(channels)}")

        print("\n" + "=" * 60)


    def get_company_by_symbol(self, symbol: str) -> Dict:
        """
        Find a specific company by its symbol.

        Args:
            config: The configuration dictionary
            symbol: Stock symbol to search for

        Returns:
            Company dictionary or None if not found
        """
        companies = self.config.get('companies', {})

        for market_name, company_list in companies.items():
            for company in company_list:
                if company['symbol'] == symbol:
                    company['market'] = market_name
                    return company

        return None


    def get_market_for_company(self, symbol: str) -> Dict:
        """
        Get the market configuration for a specific company.

        Args:
            config: The configuration dictionary
            symbol: Stock symbol

        Returns:
            Market configuration dictionary
        """
        companies = self.config.get('companies', {})
        markets = self.config.get('markets', {})

        for market_name, company_list in companies.items():
            for company in company_list:
                if company['symbol'] == symbol:
                    return markets.get(market_name, {})

        return None





    # # Example: Get all Swedish companies
    # print("\n" + "=" * 60)
    # print("Swedish Companies Details:")
    # print("=" * 60)
    # swedish_companies = get_companies(config, 'swedish')
    # for company in swedish_companies:
    #     print(f"\n{company['name']} ({company['symbol']})")
    #
    #     # Price alerts
    #     price_alerts = company.get('price_alerts', {})
    #     if price_alerts.get('enabled'):
    #         conditions = price_alerts.get('conditions', [])
    #         for condition in conditions:
    #             print(f"  📈 Price Alert: {condition['threshold_percent']}% change from {condition['comparison']}")
    #
    #     # News alerts
    #     news_alerts = company.get('news_alerts', {})
    #     if news_alerts.get('enabled'):
    #         sources = news_alerts.get('sources', [])
    #         print(f"  📰 News Sources: {', '.join(sources)}")
    #         print(f"  📰 Languages: {', '.join(news_alerts.get('languages', []))}")
    #
    # # Example: Find a specific company
    # print("\n" + "=" * 60)
    # print("Finding specific company:")
    # print("=" * 60)
    # aapl = get_company_by_symbol(config, 'AAPL')
    # if aapl:
    #     print(f"\nFound: {aapl['name']} ({aapl['symbol']})")
    #     print(f"Market: {aapl['market']}")
    #
    #     # Get market info for this company
    #     market_info = get_market_for_company(config, 'AAPL')
    #     if market_info:
    #         print(f"Exchange: {market_info['exchange']}")
    #         print(f"Currency: {market_info['currency']}")
    #         print(f"Timezone: {market_info['timezone']}")
    #         print(
    #             f"Market Hours: {market_info['market_hours']['regular']['start']} - {market_info['market_hours']['regular']['end']}")
    #
    # # Example: Get notification settings
    # print("\n" + "=" * 60)
    # print("Notification Settings:")
    # print("=" * 60)
    # notifications = get_notification_settings(config)
    # if notifications.get('enabled'):
    #     print(f"Channels: {', '.join(notifications.get('channels', []))}")
    #
    #     if 'email' in notifications.get('channels', []):
    #         email_config = notifications.get('email', {})
    #         print(f"\nEmail Configuration:")
    #         print(f"  SMTP Server: {email_config.get('smtp_server')}")
    #         print(f"  From: {email_config.get('from')}")
    #         print(f"  To: {', '.join(email_config.get('to', []))}")
