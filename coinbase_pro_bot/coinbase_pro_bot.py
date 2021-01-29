import sys
import threading
from .api_request_manager import PublicAPIRequestManager, WebsocketManager
from .portfolio_manager import PortfolioManager

PRODUCTS = [
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
]


class CoinbaseProBot(threading.Thread):

    def __init__(self):
        super().__init__()
        self.public_client = PublicAPIRequestManager()
        self.public_client.start()
        self.websocket_client = WebsocketManager(products=PRODUCTS)
        self.portfolios = []

    def shutdown(self):
        pass

    def load_portfolio(self, key_file):
        portfolio = PortfolioManager(self, key_file)
        portfolio.initialize_portfolio_manager(PRODUCTS)
        portfolio.start()
        self.portfolios.append(portfolio)

    def process_command(self, cmd):
        cmd_args = cmd.split(' ')
        if cmd_args[0] == 'portfolios':
            pass

    def start_interactive(self):
        print("Starting interactive shell for CoinbaseProBot")
        command = ""
        while command != "shutdown":
            command = input("Command: ")
        print("CoinbaseProBot shutting down")
        self.public_client.shutdown_client()
        self.websocket_client.shutdown_client()

    def add_message_to_public_client(self, msg):
        self.public_client.add_message_to_queue(msg)
