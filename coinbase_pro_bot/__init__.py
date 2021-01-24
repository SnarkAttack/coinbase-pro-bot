import logging

crypto_logger = logging.getLogger(__name__)
crypto_logger.setLevel(logging.INFO)

# create console handler and set level to debug
#ch = logging.FileHandler('logs/crypto_monitor.log')
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
crypto_logger.addHandler(ch)
