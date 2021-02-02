import sys
import threading
from .api_request_manager import PublicAPIRequestManager, WebsocketManager
from .portfolio_manager import PortfolioManager

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


class CoinbaseProBot(threading.Thread):

    def __init__(self):
        super().__init__()
        self.public_client = PublicAPIRequestManager()
        self.public_client.start()
        self.websocket_client = WebsocketManager(products=PRODUCTS)
        self.portfolios = []
        self.shutdown = False

    def shutdown(self):
        pass

    def load_portfolio(self, key_file):
        portfolio = PortfolioManager(self, key_file)
        portfolio.start()
        portfolio.initialize_portfolio_manager(PRODUCTS)
        self.portfolios.append(portfolio)

    def process_command(self, cmd):
        cmd_args = cmd.split(' ')
        if cmd_args[0] == 'portfolios':
            pass
        elif cmd_args[0] == 'state':
            states = []
            if len(cmd_args) == 1:
                for portfolio in self.portfolios:
                    states += portfolio.get_monitor_states()
                for (name, state) in states:
                    print(f"{name}: {state}")
        elif cmd_args[0] == 'rsi':
            rsi_list = []
            if len(cmd_args) == 1:
                for portfolio in self.portfolios:
                    rsi_list += portfolio.get_monitor_rsi()
                for name, rsi in rsi_list:
                    print(f"{name}: {rsi}")
        elif cmd_args[0] == 'macd_diff':
            macd_diff_list = []
            if len(cmd_args) == 1:
                for portfolio in self.portfolios:
                    macd_diff_list += portfolio.get_monitor_macd_diff()
                for name, macd_diff in macd_diff_list:
                    print(f"{name}: {macd_diff}")
        elif cmd_args[0] == 'shutdown':
            self.shutdown = True

    def start_interactive(self):
        print("Starting interactive shell for CoinbaseProBot")
        command = ""
        while not self.shutdown:
            command = input("Command: ")
            self.process_command(command)
        print("CoinbaseProBot shutting down")
        self.public_client.shutdown_client()
        self.websocket_client.shutdown_client()
        exit(0)

    def add_message_to_public_client(self, msg):
        self.public_client.add_message_to_queue(msg)
