import pytest
import sys
print(sys.path)
from coinbase_pro_bot.api_request_manager import (
    PublicAPIRequestManager, 
    AuthenticatedAPIRequestManager,
    WebsocketClient
)

def test_public_api_request_manager():
    req_man = PublicAPIRequestManager()
    response = req_man.client.get_currencies()
    print(response)