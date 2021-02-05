from talib import MACD, RSI
from .strategy import Strategy

NO_POSITION = 0
RSI_OVERSOLD = 1
BUY_INDICATED = 2
BUY = 3
POSITION_HELD = 4
RSI_OVERBOUGHT = 5
SELL_INDICATED = 6
SELL = 7

OVERSOLD_THRESHOLD = 30
OVERBOUGHT_THRESHOLD = 70


class Trade(object):

    def __init__(self, product_id, ts, price, quantity, value):
        self.product_id = product_id
        self.ts = ts
        self.price = price
        self.quantity = quantity
        self.value = value


class RsiMacdStrategy(Strategy):

    def __init__(self,
                 fast_period=12,
                 slow_period=26,
                 signal_period=9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.state = NO_POSITION
        self.cash = 10000

    def next_state(self, rsi, macd):

        next_state = self.state

        if self.state == NO_POSITION:
            if rsi <= OVERSOLD_THRESHOLD:
                next_state = RSI_OVERSOLD
        elif self.state == RSI_OVERSOLD:
            if rsi > OVERSOLD_THRESHOLD:
                next_state = BUY_INDICATED
        elif self.state == BUY_INDICATED:
            if macd > 0:
                next_state = BUY
        elif self.state == POSITION_HELD:
            if rsi >= OVERBOUGHT_THRESHOLD:
                next_state = RSI_OVERBOUGHT
        elif self.state == RSI_OVERBOUGHT:
            if rsi < OVERBOUGHT_THRESHOLD:
                next_state = SELL_INDICATED
        elif self.state == SELL_INDICATED:
            if macd < 0:
                next_state == SELL
        else:
            print(f"Unexpected state {self.state}")

        return next_state

    def execute(self, bt_env, df):
        '''
        Execute a single iteration of algorithmic trading
        '''
        last_row_idx = len(df)-1

        rsi = RSI(df.close)

        macd, macd_signal, macd_hist = MACD(df.close,
                                            fastperiod=self.fast_period,
                                            slowperiod=self.slow_period,
                                            signalperiod=self.signal_period)

        next_state = self.next_state(rsi[last_row_idx], macd[last_row_idx])

        if self.state != next_state:
            if next_state == BUY:
                # buy
                if len(bt_env.trades) == 0:
                    quantity = bt_env.balance/df.close[last_row_idx]
                    product_id = df.product_id[last_row_idx]
                    ts = df.timestamp[last_row_idx]
                    price = df.close[last_row_idx]
                    trade = Trade(
                        product_id,
                        ts,
                        price,
                        quantity,
                        bt_env.balance)
                    print(f"Bought {quantity} shares of {product_id} at "
                          f"{ts} for {price} a share (for a total of "
                          f"{bt_env.balance})")
                    bt_env.trades.append(trade)
                    bt_env.balance = 0
                    bt_env.add_buy()
                else:
                    print("already holding trade")
                self.state = POSITION_HELD
            elif next_state == SELL:
                # sell
                if len(bt_env.trades) > 0:
                    trade = bt_env.trades[0]
                    sell_price = df.close[last_row_idx]
                    sell_value = trade.quantity*sell_price
                    sell_ts = df.timestamp[last_row_idx]
                    profit = sell_value-trade.value
                    print(f"Sold {trade.quantity} shares of "
                          f"{trade.product_id} at {sell_ts} "
                          f"for {sell_price} a share (for a total "
                          f"of {sell_value}, profit of "
                          f"{profit}")
                    bt_env.balance = sell_value
                    bt_env.trades = []
                    bt_env.add_sell_value(profit)
                else:
                    print("did not have active trade")
                self.state = NO_POSITION
            else:
                self.state = next_state
