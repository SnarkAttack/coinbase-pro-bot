import sys
import threading
from api_request_manager import ApiRequestManager
from cbpro import PublicClient, AuthenticatedClient, WebsocketClient

class CoinbaseProBot(threading.Thread):

    def __init__(self):
        super().__init__(self)
        self.client = ApiRequestManager()

    def shutdown(self):
        pass

    def load_portfolio(self, key_file):
        pass

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
