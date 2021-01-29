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


class WebsocketManager(APIRequestManager):

    def __init__(self, products=None):
        super().__init__()
        self.initialize_client(self, products=products)

    def initialize_client(self, manager, products=None):
        self.client = TickerParserWebsocketClient(
            manager,
            products=products
        )
        self.client.start()

    def shutdown_client(self):
        self.client.close()
        self.client = None