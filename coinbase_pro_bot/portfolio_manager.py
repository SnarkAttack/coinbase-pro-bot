from .crypto_worker import CryptoWorker
from .api_request_manager import AuthenticatedAPIRequestManager
from .crypto_monitor import CryptoMonitor
from .crypto_logger import logger
from .crypto_message import (
    AccountBalanceRequestMessage,
    AccountBalanceResponseMessage,
)
from time import sleep
from .utilities import FIAT_MARKETS


class PortfolioManager(CryptoWorker):

    def __init__(self, bot, key_file):
        super().__init__()
        self.bot = bot
        self.client = AuthenticatedAPIRequestManager(key_file)
        self.client.start()
        self.historical_data_monitors = []
        self.trades = []

    def initialize_portfolio_manager(self, products):
        for product_id in products:
            for granularity in [3600]:
                cm = CryptoMonitor(self, product_id, granularity)
                cm.start()
                self.historical_data_monitors.append(cm)
        self.register_monitors_with_websocket_manager()

    def register_monitors_with_websocket_manager(self):
        self.bot.websocket_client.add_subscriptors(self.historical_data_monitors)

    def request_available_balance(self):
        msg = AccountBalanceRequestMessage(self, self.client)
        self.client.add_message_to_priority_queue(msg)

    def process_message(self, msg):
        if msg is not None:
            if isinstance(msg, AccountBalanceResponseMessage):
                pass
            else:
                return

    def process_messages(self):
        while self.get_remaining_message_count() > 0:
            msg = self.get_next_message_from_queue()
            self.process_message(msg)

    def run(self):
        logger.info(f"{self} starting")
        while not self.is_shutdown():
            self.process_messages()
            sleep(1)
        logger.info(f"{self} terminating")

    def add_message_to_public_client(self, msg):
        self.bot.add_message_to_public_client(msg)

    def add_message_to_authenticated_client(self, msg):
        self.client.add_message_to_queue(msg)

    def add_priority_message_to_authenticated_client(self, msg):
        self.client.add_message_to_priority_queue(msg)
        