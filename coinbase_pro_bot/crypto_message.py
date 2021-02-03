class CryptoMessage(object):

    def __init__(self, sender):
        self.sender = sender

    def __str__(self):
        return f"({self.sender} --{self.__class__.__name__}--> {self.recipient})"

    def get_name(self):
        return self.__class__.__name__


class HistoricalDataRequestMessage(CryptoMessage):

    def __init__(self, sender, product_id, granularity=None, start=None, end=None):
        super().__init__(sender)
        self.product_id = product_id
        self.granularity = granularity
        self.start = start
        self.end = end


class HistoricalDataResponseMessage(CryptoMessage):

    def __init__(self, sender, data):
        super().__init__(sender)
        self.data = data


class ProductTickerRequestMessage(CryptoMessage):

    def __init__(self, sender, product_id):
        super().__init__(sender)
        self.product_id = product_id


class ProductTickerResponseMessage(CryptoMessage):

    def __init__(self, sender, data):
        super().__init__(sender)
        self.data = data


class AccountBalanceRequestMessage(CryptoMessage):

    def __init__(self, sender):
        super().__init__(sender)


class AccountBalanceResponseMessage(CryptoMessage):

    def __init__(self, sender, data):
        super().__init__(sender)
        self.data = data


class BuyOrderRequestMessage(CryptoMessage):

    def __init__(self, sender, product_id):
        super().__init__(sender)
        self.product_id = product_id


class BuyOrderResponseMessage(CryptoMessage):

    def __init__(self, sender, data):
        super().__init__(sender)
        self.data = data


class SellOrderRequestMessage(CryptoMessage):

    def __init__(self, sender, product_id):
        super().__init__(sender)
        self.product_id = product_id


class SellOrderResponseMessage(CryptoMessage):

    def __init__(self, sender, data):
        super().__init__(sender)
        self.data = data


class ShutdownMessage(CryptoMessage):

    def __init__(self, sender):
        super().__init__(sender)


class CandleMessage(CryptoMessage):

    def __init__(self, sender, candle):
        super().__init__(sender)
        self.candle = candle
