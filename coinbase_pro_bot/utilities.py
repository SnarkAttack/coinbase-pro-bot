
from datetime import datetime, timezone

BASE_CSV_DATA = "market_data/"

FIAT_MARKETS = [
    'BTC',
    'ETH',
    'LTC',
    'BCH',
    'EOS',
    'DASH',
    'OXT',
    'MKR',
    'XLM',
    'ATOM',
    'XTZ',
    'ETC',
    'OMG',
    'ZEC',
    'LINK',
    'REP',
    'ZRX',
    'ALGO',
    'DAI',
    'KNC',
    'COMP',
    'BAND',
    'NMR',
    'CGLD',
    'UMA',
    'LRC',
    'YFI',
    'UNI',
    'REN',
    'BAL',
    'WBTC',
    'NU',
    'FIL',
    'AAVE',
    'GRT',
    'BNT',
    'SNX'
]

GRANULARITIES = [60, 300, 900, 3600, 21600, 86400]


STATE_DEFAULT = 0
STATE_OVERBOUGHT = 1
STATE_OVERSOLD = 2
STATE_SELL_INDICATED = 3
STATE_BUY_INDICATED = 4
STATE_SELL = 5
STATE_BUY = 6

RSI_OVERSOLD_THRESHOLD = 30
RSI_OVERBOUGHT_THRESHOLD = 70


def generate_file_name(pair, granularity):
    return f"{BASE_CSV_DATA}/{pair}-{granularity}.csv"


def get_newest_saved_time(pair, granularity):
    file_name = generate_file_name(pair, granularity)
    try:
        with open(file_name, 'r') as f:
            lines = f.readlines()
            if len(lines) == 0:
                return datetime.fromtimestamp(0, tz=timezone.utc)
            last_timestamp = int(lines[-1].split(',')[0])
            return datetime.fromtimestamp(last_timestamp, tz=timezone.utc)
    except FileNotFoundError:
        return datetime.fromtimestamp(0, tz=timezone.utc)