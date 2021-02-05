class Strategy(object):

    def __init__(self, start_balance=10000):
        self.start_balance = start_balance
        self.end_balance = 0

    def execute(self, data):
        raise NotImplementedError(f"{self.__class__.__name__} does not have "
                                  f"execute() defined")
