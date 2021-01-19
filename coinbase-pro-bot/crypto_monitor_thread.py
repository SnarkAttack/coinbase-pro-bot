import threading
import cbpro
from datetime import datetime, timedelta, timezone
import logging
from time import sleep
from thread_message import ThreadMessage

logger = logging.getLogger('crypto_monitor')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
#ch = logging.FileHandler('logs/crypto_monitor.log')
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


CRYPTOS = [
    'AAVE',
    'ALGO',
    'ATOM',
    'BAL',
    'BAND',
    'BAT',
    'BCH',
    'BNT',
    'BSV',
    'BTC',
    'CGLD',
    'COMP',
    'CVC',
    'DAI',
    'DASH',
    'DNT',
    'EOS',
    'ETC',
    'ETH',
    'FIL',
    'GRT',
    'GNT',
    'KNC',
    'LINK',
    'LOOM',
    'LRC',
    'LTC',
    'MANA',
    'MKR',
    'NMR',
    'NU',
    'OMG',
    'OXT',
    'REN',
    'REP',
    'SNX',
    'USDC',
    'UMA',
    'UNI',
    'WBTC',
    'XLM',
    'XRP',
    'XTZ',
    'YFI',
    'ZEC',
    'ZRX',
]
BASE_CSV_DATA = "market_data/"

GRANULARITIES = [60, 300, 900, 3600, 21600, 86400]

def generate_file_name(pair, granularity):
    return f"{BASE_CSV_DATA}/{pair}_{granularity}.csv"

def get_newest_saved_time(pair, granularity):
    file_name = generate_file_name(pair, granularity)
    try:
        with open(file_name, 'r') as f:
            lines = f.readlines()
            if len(lines) == 0:
                return datetime.fromtimestamp(0, tz=timezone.utc)
            last_timestamp = int(lines[-1].split(',')[0])
            return datetime.fromtimestamp(last_timestamp, tz=timezone.utc)
    except FileNotFoundError:
        return datetime.fromtimestamp(0, tz=timezone.utc)

class CryptoMonitorManager(object):

    def __init__(self):
        self.client = cbpro.PublicClient()
        self.threads = []
        self.message_queue = []
        self.message_queue_lock = threading.Lock()

    def __repr__(self):
        return f"CryptoMonitorManager1"

    def start_monitoring(self, cryptos=[]):
        if len(cryptos) == 0:
            crypto_list = [f"{crypto}-USD" for crypto in CRYPTOS]
        else:
            valid_cryptos = [crypto for crypto in cryptos if crypto in CRYPTOS]
            crypto_list = [f"{crypto}-USD" for crypto in valid_cryptos]

        for crypto_pair in crypto_list:
            thread = CryptoMonitorThread(crypto_pair, self)
            self.threads.append(thread)
            thread.start()

    def add_message_to_queue(self, msg):
        ret_val = 0
        self.message_queue_lock.acquire()
        for waiting_cmm in self.message_queue:
            if msg.is_message_match(waiting_cmm):
                ret_val = 1
                break
        if ret_val == 0:
            self.message_queue.append(msg)
            logger.info(f"Message {msg} added to manager queue")
        else:
            logger.debug(f"Message not added because duplicate found")
        self.message_queue_lock.release()
        return 0

    def process_next_message_in_queue(self):
        self.message_queue_lock.acquire()
        if len(self.message_queue) > 0:
            msg = self.message_queue.pop(0)
            logger.info(f"{self} processing message {msg}")
            logger.debug(f"Messages left in {self} queue: {len(self.message_queue)}")
            crypto_data = self.client.get_product_historic_rates(msg.pair,
                                                                 start=msg.iso_time,
                                                                 granularity=msg.granularity)
            try:
                crypto_data.sort(key=lambda x: x[0])
            except AttributeError as e:
                logger.error("Did not get response in expected format, aborting")
            return_msg = CryptoMonitorResultsMessage(self, msg.sender, msg.granularity, crypto_data)
            msg.sender.add_message_to_queue(return_msg)
        else:
            logger.debug(f"No messages in {self} queue")
        self.message_queue_lock.release()


class CryptoMonitorRequestMessage(ThreadMessage):

    def __init__(self, sender, recipient, pair, granularity, iso_time):
        super().__init__(sender, recipient)
        self.pair = pair
        self.granularity = granularity
        self.iso_time = iso_time

    def is_message_match(self, cmm):
        return self.pair == cmm.pair and self.granularity == cmm.granularity


class CryptoMonitorResultsMessage(ThreadMessage):

    def __init__(self, sender, recipient, granularity, results):
        super().__init__(sender, recipient)
        self.granularity = granularity
        self.results = results

class CryptoMonitorThread(threading.Thread):

    def __init__(self, pair, crypto_manager):
        super().__init__()
        self.pair = pair
        self.crypto_manager = crypto_manager
        self.message_queue = []
        self.message_queue_lock = threading.Lock()
        self.start_time = datetime.now(tz=timezone.utc)
        self.last_timestamps = {}

    def __repr__(self):
        return f"Thread-{self.pair}"

    def process_message_queue(self):
        while len(self.message_queue) > 0:
            msg = self.message_queue.pop(0)
            logger.debug(f"{self} processing {msg}")
            self.save_crypto_data(msg)

    def request_crypto_data(self, granularity):
        logger.info(f"{self} requesting update for {self.pair} at granularity {granularity}")
        message = CryptoMonitorRequestMessage(self,
                                              self.crypto_manager,
                                              self.pair,
                                              granularity,
                                              self.last_timestamps[granularity].isoformat()
                                              )
        self.crypto_manager.add_message_to_queue(message)
        return

    def save_crypto_data(self, msg):
        file_name = generate_file_name(self.pair, msg.granularity)
        with open(file_name, "a+") as f:
            f.seek(0)
            lines = f.readlines()
            for pair_line_data in msg.results:
                csv_line = ','.join([str(x) for x in pair_line_data]) + "\n"
                if csv_line not in lines:
                    f.write(csv_line)
                    ts = int(csv_line.split(',')[0])
                    self.last_timestamps[msg.granularity] = datetime.fromtimestamp(ts, tz=timezone.utc)

    def add_message_to_queue(self, msg):
        self.message_queue_lock.acquire()
        self.message_queue.append(msg)
        logger.info(f"Message {msg} added to monitor thread queue")
        self.message_queue_lock.release()
        return 0

    def run(self):
        logger.info(f"{self.pair} starting")

        granularities = GRANULARITIES

        for granularity in granularities:
            self.last_timestamps[granularity] = get_newest_saved_time(self.pair, granularity)

        while(True):
            self.process_message_queue()
            for granularity in granularities:
                now = datetime.now(tz=timezone.utc)
                if now > self.last_timestamps[granularity]+timedelta(seconds=granularity*5):
                    logger.error(f"{now} > {self.last_timestamps[granularity]+timedelta(seconds=granularity*5)}")
                    logger.debug(f"{self} determined it is time to request new data for granularity {granularity}")
                    self.request_crypto_data(granularity)
            sleep(1)


if __name__ == "__main__":
    crypto_mon = CryptoMonitorManager()
    crypto_mon.start_monitoring(cryptos=['ETH', 'LINK'])

    while True:
        crypto_mon.process_next_message_in_queue()
        sleep(.5)
