from crypto_worker import CryptoWorker
from api_request_manager import ApiRequestManager
from crypto_monitor import CryptoMonitor
from crypto_logger import logger
from crypto_message import (
    AccountBalanceRequestMessage,
    AccountBalanceResponseMessage,
)
from time import sleep

MAX_INVESTMENT = 10

class PortfolioManager(CryptoWorker):

    def __init__(self, key_file):
        super().__init__(self)
        self.client = ApiRequestManager(key_file)
        self.client .start()
        self.historical_data_monitors = []

    def initialize_portfolio_manager(self):
        cm = CryptoMonitor(self.client, "ETH-USD", 3600)
        cm.start()
        self.historical_data_monitors.append(cm)

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
        #self.initialize_portfolio_manager()
        self.request_available_balance()
        while not self.is_shutdown():
            self.process_messages()
            sleep(1)
        logger.info(f"{self} terminating")


if __name__ == "__main__":
    pf = PortfolioManager('3600coinbasebot.key')
    pf.start()
