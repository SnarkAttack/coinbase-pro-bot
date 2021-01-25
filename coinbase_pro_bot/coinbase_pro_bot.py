import sys
import threading
from api_request_manager import PublicAPIRequestManager, WebsocketManager
from portfolio_manager import PortfolioManager


class CoinbaseProBot(threading.Thread):

    def __init__(self):
        super().__init__(self)
        self.public_client = PublicAPIRequestManager()
        self.websocket_client = WebsocketManager(products=['ETH-USD'])
        self.portfolios = []

    def shutdown(self):
        pass

    def load_portfolio(self, key_file):
        self.portfolios = PortfolioManager(key_file)

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
