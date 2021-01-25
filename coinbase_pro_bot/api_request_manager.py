from time import sleep
from cbpro import PublicClient, AuthenticatedClient, WebsocketClient
from .crypto_worker import PriorityCryptoWorker
from .crypto_message import *
from .crypto_logger import logger
import simplejson as json

MAX_INVESTMENT = 10


class APIRequestManager(PriorityCryptoWorker):

    def __init__(self):
        super().__init__()
        self.client = None

class PublicAPIRequestManager(APIRequestManager):

    def __init__(self):
        super().__init__()
        self.initialize_client()

    def initialize_client(self):
        self.client = PublicClient()


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


class TickerParserWebsocketClient(WebsocketClient):

    def __init__(self, products=None):
        super().__init__(products, channels=["ticker"])

    def on_open(self):
        logger.info("Websocket subscribed")

    def on_message(self, msg):
        print(json.dumps(msg, indent=4, sort_keys=True))

    def on_close(self):
        logger.info("Websocket closed")


class WebsocketManager(APIRequestManager):

    def __init__(self):
        super().__init__()
        self.initialize_client()

    def initialize_client(self, products=None):
        self.client = TickerParserWebsocketClient(
            products=products
        )


class ApiRequestManager(PriorityCryptoWorker):

    def __init__(self, key_file):
        super().__init__(self)
        self.key = None
        self.b64secret = None
        self.passphrase = None
        self.client = None

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

    def get_next_message(self):
        msg = self.get_next_message_from_priority_queue()
        if msg is None:
            msg = self.get_next_message_from_queue()
        return msg

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

    def process_product_ticker_request(self, msg):

        product_ticker_data = self.client.get_product_ticker(
            msg.product_id
        )

        response_msg = ProductTickerResponseMessage(
            msg.recipient,
            msg.sender,
            product_ticker_data
        )

        msg.sender.add_message_to_queue(response_msg)

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

        logger.info(buy_order_response)

    def process_sell_order_request(self, msg):

        sell_order_response = self.client.place_market_order(
            msg.product_id,
            'sell',
            size
        )


    def process_next_message(self):
        msg = self.get_next_message()
        if msg is not None:
            if isinstance(msg, HistoricalDataRequestMessage):
                self.process_historical_data_request(msg)
            if isinstance(msg, ProductTickerRequestMessage):
                self.process_product_ticker_request(msg)
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
            sleep(1/3)
        logger.info("DONE")

