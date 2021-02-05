from cbpro_candles.candle_db import CoinbaseProCandleDatabase
from backtest.backtest import Backtester, BacktesterEnv
from strategy.macd_strategy import MacdStrategy
from strategy.rsi_macd_strategy import RsiMacdStrategy
import argparse

db_file = "../cbpro_candles/candles_all.db"

PRODUCTS = sorted([
    "BTC-USD",
    "ETH-USD",
    "LTC-USD",
    "BCH-USD",
    "EOS-USD",
    "DASH-USD",
    "OXT-USD",
    "MKR-USD",
    "XLM-USD",
    "ATOM-USD",
    "XTZ-USD",
    "ETC-USD",
    "OMG-USD",
    "ZEC-USD",
    "LINK-USD",
    "REP-USD",
    "ZRX-USD",
    "ALGO-USD",
    "DAI-USD",
    "KNC-USD",
    "COMP-USD",
    "BAND-USD",
    "NMR-USD",
    "CGLD-USD",
    "UMA-USD",
    "LRC-USD",
    "YFI-USD",
    "UNI-USD",
    "REN-USD",
    "BAL-USD",
    "WBTC-USD",
    "NU-USD",
    "FIL-USD",
    "AAVE-USD",
    "GRT-USD",
    "BNT-USD",
    "SNX-USD"
])

GRANULARITIES = [60, 300, 900, 3600, 21600, 86400]

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    list_of_strategies = ['macd', 'rsi_macd']

    parser.add_argument('-s', '--strategy',
                        help='Type of strategy to use',
                        choices=list_of_strategies,
                        default='macd')
    parser.add_argument('-p', '--products',
                        help='Comma separated list of products to test',
                        choices=PRODUCTS,
                        default='ETH-USD')
    parser.add_argument('-g', '--granularity',
                        help='Granularity (in seconds) to backtest on',
                        type=int,
                        choices=GRANULARITIES,
                        default=3600)
    parser.add_argument('-b', '--start_balance',
                        type=int,
                        help='Starting balance to use',
                        default=10000)
    parser.add_argument('-c', '--candles_count',
                        type=int,
                        help='Number of candles to use in calculations',
                        default=300)

    args = parser.parse_args()

    products = args.products.split(',')

    backtester = Backtester()

    for product_id in products:

        back_env = BacktesterEnv(db_file,
                                 product_id,
                                 args.granularity,
                                 start_balance=args.start_balance)

        if args.strategy == 'macd':
            strategy = MacdStrategy()
        elif args.strategy == 'rsi_macd':
            strategy = RsiMacdStrategy()

        backtester.backtest(back_env, strategy)
