class CryptoMessage(object):

    def __init__(self, sender, recipient):
        self.sender = sender
        self.recipient = recipient

    def __str__(self):
        return f"({self.sender} --{self.__class__.__name__}--> {self.recipient})"


class HistoricalDataRequestMessage(CryptoMessage):

    def __init__(self, sender, recipient, product_id, granularity=None, start=None, end=None):
        super().__init__(sender, recipient)
        self.product_id = product_id
        self.granularity = granularity
        self.start = start
        self.end = end


class HistoricalDataResponseMessage(CryptoMessage):

    def __init__(self, sender, recipient, data):
        super().__init__(sender, recipient)
        self.data = data


class ProductTickerRequestMessage(CryptoMessage):

    def __init__(self, sender, recipient, product_id):
        super().__init__(sender, recipient)
        self.product_id = product_id


class ProductTickerResponseMessage(CryptoMessage):

    def __init__(self, sender, recipient, data):
        super().__init__(sender, recipient)
        self.data = data


class AccountBalanceRequestMessage(CryptoMessage):

    def __init__(self, sender, recipient):
        super().__init__(sender, recipient)


class AccountBalanceResponseMessage(CryptoMessage):

    def __init__(self, sender, recipient, data):
        super().__init__(sender, recipient)
        self.data = data


class BuyOrderRequestMessage(CryptoMessage):

    def __init__(self, sender, recipient, product_id):
        super().__init__(sender, recipient)
        self.product_id = product_id


class BuyOrderResponseMessage(CryptoMessage):

    def __init__(self, sender, recipient, data):
        super().__init__(sender, recipient)
        self.data = data


class SellOrderRequestMessage(CryptoMessage):

    def __init__(self, sender, recipient, product_id):
        super().__init__(sender, recipient)
        self.product_id = product_id


class SellOrderResponseMessage(CryptoMessage):

    def __init__(self, sender, recipient, data):
        super().__init__(sender, recipient)
        self.data = data


class ShutdownMessage(CryptoMessage):

    def __init__(sender, recipient):
        super().__init__(sender, recipient)
