from time import sleep
from datetime import datetime, timezone
import dateutil.parser
from decimal import Decimal
import numpy as np

from crypto_worker import CryptoWorker
from crypto_logger import logger
from crypto_message import (
    ShutdownMessage,
    CandleMessage,
)

DOWNWARD_TREND = 1
UPWARD_TREND = 2
INDECISIVE_TREND = 4


class Candle(object):

    def __init__(self, open, high, low, close):
        self.open = open
        self.high = high
        self.low = low
        self.close = close

     @property
    def shadow(self):
        return self.high-self.low

    @property
    def upper_shadow(self):
        return self.high-self.open

    @property
    def lower_shadow(self):
        return self.close-self.low

    @property
    def body(self):
        return self.open-self.close

    @property
    def midprice(self):
        return (self.high+self.low)/2

    def bull(self):
        return self.close > self.open

    def bear(self):
        return self.close <self.open

    def doji(self, doji_ratio=.05):
        return self.body/self.shadow <= doji_ratio


class CandlestickPattern(object):

    def __init__(self, length, signal):
        self.length = length
        self.signal = signal

    def pattern_match(self, candles):
        raise NotImplementedError(f"{self.__class__.__name__} does not have "
                                  f"a pattern_match function")


class Hammer(CandlestickPattern):

    def __init__(self,
                 lower_shadow_ratio=.5,
                 upper_shadow_ratio=.25,
                 body_ratio=.25):
        super().__init__(1, UPWARD_TREND)
        self.lower_shadow_ratio = lower_shadow_ratio
        self.upper_shadow_ratio = upper_shadow_ratio
        self.body_ratio = body_ratio

    def pattern_match(self, candles):
        hammer_candle = candles[-1]
        upper_shadow_check = (hammer_candle.upper_shadow/hammer_candle.shadow) <= self.lower_shadow_ratio
        lower_shadow_check = (hammer_candle.lower_shadow/hammer_candle.shadow) >= self.upper_shadow_ratio
        body_check = (hammer_candle.body/hammer_candle.shadow) <= self.body_ratio
        return upper_shadow_check and lower_shadow_check and body_check

class EngulfingBull(CandlestickPattern):

    def __init__(self):
        super().__init__(2, UPWARD_TREND)

    def pattern_match(self, candles):
        small_bear = candles[-2]
        large_bull = candles[-1]

        if not small_bear.bear() or not large_bull.bull():
            return False

        return (small_bear.close > large_bull.close) and (small_bear.open > large_bull.open)

class PiercingLine(CandlestickPattern):

    def __init__(self,
                 bear_body_ratio=.75,
                 bull_body_ratio=.75):
        super().__init__(2, UPWARD_TREND)
        self.bear_body_ratio = bear_body_ratio
        self.bull_body_ratio = bull_body_ratio

    def pattern_match(self, candles):
        bear = candles[-2]
        bull = candles[-1]

        # Make sure bear and bull candles are actually bear and bull
        if not bear.bear() or not bull.bull():
            return False

        # Check the bear body is greater than the bear body ratio
        if bear.body/bear.shadow < self.bear_body_ratio:
            return False

        # Check the bull body is greater than the bull body ratio
        if bull.body/bull.shadow < self.bull_body_ratio:
            return False

        # The close on the bull bar must be above the midpoint of the bear bar
        if bull.close > bear.midpoint:
            return False

        return True


class Morningstar(CandlestickPattern):

    def __init__(self,
                 bear_body_ratio=.75,
                 bull_body_ratio=.75,
                 doji_ratio=.05):
        super().__init__(3, UPWARD_TREND)
        self.bear_body_ratio = bear_body_ratio
        self.bull_body_ratio = bull_body_ratio
        self.doji_ratio = doji_ratio

    def pattern_match(self, candles):
        bear = candles[-3]
        doji = candles[-2]
        bull = candles[-1]

        # Check that bear, doji, and bull are what they must be
        if not bear.bear() or not bull.bull() or not doji.doji():
            return False

        # Check bear body is over ratio
        if bear.body/bear.shadow < self.bear_body_ratio:
            return False

        # Check bull body is over ratio
        if bull.body/bull.shadow < self.bull_body_ratio:
            return False

        # The "morningstar" body should not overlap with the bodies
        # either the bear or bull bodies
        if doji.bear():
            if doji.open > bear.close or doji.open > bull.close:
                return False
        else:
            if doji.close > bear.close or doji.close > bull.close:
                return False

        return True





class CandlestickMonitor(CryptoWorker):

    max_candles = 10

    def __init__(self, client, product_id, granularity):
        super().__init__(client)
        self.product_id = product_id
        self.granularity = granularity
        self.candles = []

    def __str__(self):
        return f"{self._class__.__name__}({self.get_thread_name()},{self.product_id},{self.granularity})"

    def process_message(self, msg):
        if msg is not None:
            if isinstance(msg, CandleMessage):
                # Check if the most recent time is from after our last most recent
                # If it is, build a new dataframe and save it. If not, we'll keep
                # trying until it is
                candle = msg.candle
                if len(self.candles) == CandlestickMonitor.max_candles:
                    self.candles.pop(0)
                    self.candles.append(candle)

            else:
                logger.warning(f"{self.get_name()} received message {msg.get_name()} "
                               f"which it does not know how to process")

    def evaluate_candlestick_signal(self):
        if len(self.candles) >= 2:

    def process_messages(self):
        while self.get_remaining_message_count() > 0:
            msg = self.get_next_message_from_queue()
            self.process_message(msg)

    def run(self):
        logger.info(f"{self} starting")
        while not self.is_shutdown():
            self.process_messages()
            sleep(1)
        logger.info(f"{self} terminating")
