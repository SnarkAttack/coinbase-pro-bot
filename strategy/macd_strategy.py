from talib import MACD
from .strategy import Strategy
from backtest.backtest import Trade

MACD_HIGH = 0
MACD_LOW = 1


class MacdStrategy(Strategy):

    def __init__(self,
                 fast_period=12,
                 slow_period=26,
                 signal_period=9):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.signal = None
        self.trade = None

    def execute(self, bt_env, df):

        last_row_idx = len(df)-1

        macd, macd_signal, macd_hist = MACD(df.close,
                                            fastperiod=self.fast_period,
                                            slowperiod=self.slow_period,
                                            signalperiod=self.signal_period)

        macd_state = MACD_HIGH if macd_hist[last_row_idx] > 0 else MACD_LOW

        if self.signal is None:
            self.signal = macd_state
        elif self.signal != macd_state:
            if macd_state == MACD_HIGH:
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
            elif macd_state == MACD_LOW:
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
            self.signal = macd_state
