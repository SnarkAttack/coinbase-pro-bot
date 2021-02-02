from time import sleep
from cbpro import PublicClient, AuthenticatedClient, WebsocketClient
from .crypto_worker import PriorityCryptoWorker
from .crypto_message import (
    HistoricalDataRequestMessage,
    HistoricalDataResponseMessage,
    ProductTickerResponseMessage,
    AccountBalanceRequestMessage,
    AccountBalanceResponseMessage,
    BuyOrderRequestMessage,
    SellOrderRequestMessage,
)
from .crypto_logger import logger
import simplejson as json
from datetime import datetime, timezone, timedelta
import dateutil.parser
from decimal import Decimal

MAX_INVESTMENT = 10
TICKER_UPDATE_INTERVAL = 30


class APIRequestManager(PriorityCryptoWorker):

    def __init__(self):
        super().__init__()
        self.client = None
        self.subscriptors = []

    def add_subscriptor(self, subscriptor):
        self.subscriptors.append(subscriptor)

    def add_subscriptors(self, subscriptors):
        for subscriptor in subscriptors:
            self.add_subscriptor(subscriptor)

    def remove_subscriptor(self, subscriptor):
        self.subscriptors.remove(subscriptor)

    def remove_subscriptors(self, subscriptors):
        for subscriptor in subscriptors:
            self.remove_subscriptor(subscriptor)

    def get_interested_subscriptors(self, interest_cond):
        interested_subscriptors = []
        for subscriptor in self.subscriptors:
            if interest_cond(subscriptor):
                interested_subscriptors.append(subscriptor)
        return interested_subscriptors

    def get_next_message(self):
        msg = self.get_next_message_from_priority_queue()
        if msg is None:
            msg = self.get_next_message_from_queue()
        return msg

    def shutdown_client(self):
        self.client = None


class PublicAPIRequestManager(APIRequestManager):

    def __init__(self):
        super().__init__()
        self.initialize_client()

    def initialize_client(self):
        self.client = PublicClient()

    def process_historical_data_request(self, msg):

        historical_data = self.client.get_product_historic_rates(
            msg.product_id,
            start=msg.start,
            end=msg.end,
            granularity=msg.granularity
        )

        response_msg = HistoricalDataResponseMessage(
            msg.recipient,
            msg.sender,
            historical_data
        )
        msg.sender.add_message_to_queue(response_msg)

    def process_next_message(self):
        msg = self.get_next_message()
        if msg is not None:
            if isinstance(msg, HistoricalDataRequestMessage):
                self.process_historical_data_request(msg)
            else:
                logger.error(f"Unexpected {msg.__class__.__name__} received "
                             f"by {self}")

    def run(self):
        logger.info(f"{self} starting")
        while not self.is_shutdown():
            self.process_next_message()
            sleep(1/3)
        logger.info("DONE")


class AuthenticatedAPIRequestManager(APIRequestManager):

    def __init__(self, key_file=None):
        super().__init__()
        if key_file is not None:
            self.load_keys_from_file(key_file)
            self.initialize_client()

    def load_keys_from_file(self, key_file):
        with open(key_file, 'r') as f:
            lines = f.readlines()
            [self.key, self.b64secret, self.passphrase] = [x.strip() for x in lines][:3]

    def initialize_client(self):
        self.client = AuthenticatedClient(
            self.key,
            self.b64secret,
            self.passphrase
        )

    def process_account_balance_request(self, msg):

        account_balance_data = self.client.get_accounts()

        response_msg = AccountBalanceResponseMessage(
            msg.recipient,
            msg.sender,
            account_balance_data
        )

        msg.sender.add_message_to_queue(response_msg)

    def process_buy_order_request(self, msg):

        buy_order_response = self.client.place_market_order(
            msg.product_id,
            'buy',
            funds=MAX_INVESTMENT,
        )

        logger.info(json.dumps(buy_order_response, indent=4))

    def process_sell_order_request(self, msg):

        sell_order_response = self.client.place_market_order(
            msg.product_id,
            'sell',
            size
        )

        logger.info(json.dumps(sell_order_response, indent=4))

    def process_next_message(self):
        msg = self.get_next_message()
        if msg is not None:
            if isinstance(msg, AccountBalanceRequestMessage):
                self.process_account_balance_request(msg)
            if isinstance(msg, BuyOrderRequestMessage):
                self.process_buy_order_request(msg)
            if isinstance(msg, SellOrderRequestMessage):
                self.process_sell_order_request(msg)

    def run(self):
        logger.info(f"{self} starting")
        while not self.is_shutdown():
            self.process_next_message()
            sleep(1/5)
        logger.info("DONE")


class TickerParserWebsocketClient(WebsocketClient):

    def __init__(self, manager, products=None):
        super().__init__(products=products, channels=["ticker"])
        self.manager = manager
        self.products = products
        self.last_message_sent = {}
        for product in products:
            self.last_message_sent[product] = datetime.fromtimestamp(0, tz=timezone.utc)

    def on_open(self):
        logger.info("Websocket subscribed")

    def on_message(self, msg):
        if msg['type'] == 'ticker':
            product_id = msg['product_id']
            ts = dateutil.parser.isoparse(msg['time'])
            if ts > self.last_message_sent[product_id] + timedelta(seconds=30):
                self.last_message_sent[product_id] = ts
                for sub in self.manager.get_interested_subscriptors(lambda x: x.product_id == product_id):
                    resp_msg = ProductTickerResponseMessage(self.manager, sub, msg)
                    sub.add_message_to_queue(resp_msg)

    def on_close(self):
        logger.info("Websocket closed")


class Candle(object):

    def __init__(self, product_id, time=datetime.fromtimestamp(0, tz=timezone.utc)):
        self.product_id = product_id
        self.ts = time
        self.open = None
        self.high = None
        self.low = None
        self.close = None
        self.prev_candle = None
        self.next_candle = None

    def update_candle(self, price):
        dec_price = Decimal(price)
        if self.open is None:
            self.open = dec_price
        if self.high is None or self.high < dec_price:
            self.high = dec_price
        if self.low is None or self.low > dec_price:
            self.low = dec_price
        self.close = dec_price

    def doji_eval(self):
        body_size = Decimal(abs(self.open-self.close))
        shadow_size = Decimal(self.high-self.low)
        if body_size != 0 and shadow_size != 0 and 20 * body_size <= shadow_size:
            self.print()
            # Is doji
            body_center = (self.open+self.close)/2
            print(f"Body center: {body_center}")
            print(f"Low threshold: {self.low + Decimal(1/3)*shadow_size}")
            print(f"High threshold: {self.low + Decimal(2/3)*shadow_size}")
            print(f"Under low: {body_center < self.low + Decimal(1/3)*shadow_size}")
            print(f"Over high: {body_center > self.low + Decimal(2/3)*shadow_size}")
            if body_center < self.low + Decimal(1/3)*shadow_size:
                return (True, 'gravestone')
            elif body_center > self.low + Decimal(2/3)*shadow_size:
                return (True, 'dragonfly')
            else:
                return (True, 'doji')
        else:
            return (False, None)

    def candle_to_str(self):
        return (
            f"{self.product_id} @ {self.ts}:\n"
            f"\tOpen: {self.open}\n"
            f"\tHigh: {self.high}\n"
            f"\tLow: {self.low}\n"
            f"\tClose: {self.close}"
        )

    def print(self):
        print(self.candle_to_str())


class CandleBuilderWebsocketClient(WebsocketClient):
    def __init__(self, manager, products=None):
        super().__init__(products=products, channels=["ticker"])
        self.manager = manager
        self.products = products
        self.candles = {}
        for product in products:
            self.candles[product] = []

    def on_open(self):
        logger.info("CandleBuilderWebsocketClient subscribed")

    def on_message(self, msg):
        if msg['type'] == 'ticker':
            product_id = msg['product_id']
            ts = dateutil.parser.isoparse(msg['time']).replace(second=0, microsecond=0)
            if len(self.candles[product_id]) > 0:
                if ts > self.candles[product_id][-1].ts:
                    (is_doji, doji_type) = self.candles[product_id][-1].doji_eval()
                    if is_doji:
                        print(f"{product_id} displayed a {doji_type} at start of {ts}\n")
                    self.candles[product_id].append(Candle(product_id, ts))
            else:
                self.candles[product_id].append(Candle(product_id, ts))
            self.candles[product_id][-1].update_candle(msg['price'])

    def on_close(self):
        logger.info("CandleBuilderWebsocketClient closed")

    def get_last_complete_candle(self, product):
        if self.candles.get(product) is None:
            return None
        if len(self.candles[product]) > 1:
            return self.candles[product][-2]
        return None

    def get_current_candle(self, product):
        if self.candles.get(product) is None:
            return None
        if len(self.candles[product]) > 0:
            return self.candles[product][-1]
        return None


class WebsocketManager(APIRequestManager):

    def __init__(self, products=None, client_type='ticker_parser'):
        super().__init__()
        if client_type == 'ticker_parser':
            self.initialize_ticker_parser_client(self, products=products)
        elif client_type == 'candle_builder':
            self.initialize_candle_builder_client(self, products=products)

    def initialize_ticker_parser_client(self, manager, products=None):
        self.client = TickerParserWebsocketClient(
            manager,
            products=products
        )
        self.client.start()

    def initialize_candle_builder_client(self, manager, products=None):
        self.client = CandleBuilderWebsocketClient(
            manager,
            products=products
        )
        self.client.start()

    def shutdown_client(self):
        self.client.close()
        self.client = None
