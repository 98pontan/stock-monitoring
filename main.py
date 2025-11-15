from config import StockConfig
import asyncio
from http_handlers.alphavantage_api import AlphaVantageApi
from us_stock_manager.run import StockManagerUS
import tracemalloc


async def main():

    config_file = "config.yaml"
    stock_config = StockConfig(config_file)
    #stock_config.print_config_summary()

    #print(stock_config.get_markets())
    alphavantage_api = AlphaVantageApi()
    market = stock_config.get_markets()
    print(market)
    StockManager = StockManagerUS(config=stock_config, us_stock_api=alphavantage_api)
    await StockManager.run()

if __name__ == '__main__':
    asyncio.run(main())