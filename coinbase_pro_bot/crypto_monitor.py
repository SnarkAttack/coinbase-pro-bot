from time import sleep
from datetime import datetime, timedelta, timezone
import dateutil.parser
from decimal import Decimal
import numpy as np

from .crypto_worker import CryptoWorker
from .crypto_message import (
    ShutdownMessage,
    HistoricalDataRequestMessage,
    HistoricalDataResponseMessage,
    ProductTickerRequestMessage,
    ProductTickerResponseMessage,
    BuyOrderRequestMessage,
    BuyOrderResponseMessage,
    SellOrderRequestMessage,
    SellOrderResponseMessage,
)
from .crypto_logger import logger
from .data_processing import (
    gather_all_crypto_data, 
    list_to_dataframe, 
    determine_next_state, 
    save_graphs,
    check_macd_diff,
    check_rsi,
)
from .utilities import (
    STATE_DEFAULT,
    STATE_OVERBOUGHT,
    STATE_OVERSOLD,
    STATE_SELL_INDICATED,
    STATE_BUY_INDICATED,
    STATE_SELL,
    STATE_BUY,
)

SLEEP_TIME = 30
SLEEP_INTERVAL = 5

class CryptoMonitor(CryptoWorker):

    def __init__(self, portfolio, product_id, granularity):
        super().__init__()
        self.portfolio = portfolio
        self.product_id = product_id
        self.granularity = granularity
        self.last_time = datetime.fromtimestamp(0, tz=timezone.utc)
        self.historical_df = None
        self.state = STATE_DEFAULT
        self.owned_crypto_balance = Decimal(0)
        self.last_ticker_df = None

    def __str__(self):
        return f"CryptoMonitor({self.get_thread_name()},{self.product_id},{self.granularity})"

    def round_down_time(self, t):
        return t.replace(microsecond=0, second=0, minute=0, tzinfo=timezone.utc)

    def get_expected_last_time(self):
        return self.round_down_time(datetime.utcnow())

    def request_data(self):
        if datetime.now(tz=timezone.utc) > self.last_time + timedelta(minutes=5):
            history_request_msg = HistoricalDataRequestMessage(
                self,
                "PublicClient",
                self.product_id,
                granularity=self.granularity,
            )
            self.portfolio.add_message_to_public_client(history_request_msg)

    def get_current_rsi(self):
        if self.last_ticker_df is not None:
            return self.last_ticker_df.loc[len(self.last_ticker_df)-1, 'rsi']
        else:
            return "Unavailable"

    def get_current_macd(self):
        if self.last_ticker_df is not None:
            return self.last_ticker_df.loc[len(self.last_ticker_df)-1, 'macd']
        else:
            return "Unavailable"

    def get_current_macd_diff(self):
        if self.last_ticker_df is not None:
            return self.last_ticker_df.loc[len(self.last_ticker_df)-1, 'macd']-self.last_ticker_df.loc[len(self.last_ticker_df)-1, 'macd_sig']
        else:
            return "Unavailable"

    def process_message(self, msg):
        if msg is not None:
            if isinstance(msg, HistoricalDataResponseMessage):
                self.historical_df = list_to_dataframe(msg.data)
                self.last_time = datetime.now(tz=timezone.utc)
            elif isinstance(msg, ProductTickerResponseMessage):
                if self.historical_df is None:
                    return None
                fresh_df = self.historical_df.copy(deep=True)
                dt = dateutil.parser.isoparse(msg.data['time'])
                d = "{:.2f}".format(float(msg.data['price']))
                fresh_df.loc[len(fresh_df)] = [dt, 0, 0, 0, Decimal(d), 0]
                df = gather_all_crypto_data(fresh_df)
                self.last_ticker_df = df
                z = np.polyfit(df.index, [float(x) for x in df.close], 1)
                if Decimal(z[0])/Decimal(d) < Decimal(-0.005):
                    logger.warning(f"{self} has a significantly negative trend, "
                                    f"avoiding this market for now")
                    return
                next_state = determine_next_state(df, self.state)
                if next_state == STATE_BUY:
                    if self.owned_crypto_balance.compare(Decimal(0)) == Decimal(1):
                        logger.info(f"{self} already has a outstanding balance "
                                    f"of {self.owned_crypto_balance}")
                    else:
                        logger.info(f"{self} is issuing a buy order")
                        buy_order = BuyOrderRequestMessage(self, self.client, self.product_id)
                        self.client.add_message_to_priority_queue(buy_order)
                        self.state = STATE_DEFAULT
                elif next_state == STATE_SELL:
                    if self.owned_crypto_balance.compare(Decimal(0)) == Decimal(0):
                        logger.info(f"{self} does not have any outstanding "
                                    f"crypto to sell")
                    else:
                        logger.info(f"{self} is issuing a sell order")
                        sell_order = SellOrderRequestMessage(self, self.client, self.product_id)
                        self.client.add_message_to_priority_queue(sell_order)
                        self.state = STATE_DEFAULT
                else:
                    if next_state != STATE_DEFAULT and next_state != self.state:
                        logger.info(f"{self} has just entered state {next_state}")
                    self.state = next_state
            elif isinstance(msg, BuyOrderResponseMessage):
                self.owned_crypto_balance = Decimal(msg['size'])
            elif isinstance(msg, SellOrderResponseMessage):
                self.owned_crypto_balance = Decimal(0)
            else:
                return

    def process_messages(self):
        while self.get_remaining_message_count() > 0:
            msg = self.get_next_message_from_queue()
            self.process_message(msg)

    def run(self):
        logger.info(f"{self} starting")
        while not self.is_shutdown():
            self.request_data()
            for i in range(int(SLEEP_TIME/SLEEP_INTERVAL)):
                self.process_messages()
                sleep(SLEEP_INTERVAL)
        logger.info(f"{self} terminating")
