import threading
from crypto_logger import logger


class CryptoWorker(threading.Thread):

    def __init__(self, client):
        super().__init__()
        self.msg_queue = []
        self.msg_lock = threading.Lock()
        self.shutdown = False
        self.client = client

    def get_remaining_message_count(self):
        self.msg_lock.acquire()
        count = len(self.msg_queue)
        self.msg_lock.release()
        return count

    def add_message_to_queue(self, msg):
        self.msg_lock.acquire()
        logger.info(msg)
        self.msg_queue.append(msg)
        self.msg_lock.release()

    def get_next_message_from_queue(self):
        msg = None
        self.msg_lock.acquire()
        if len(self.msg_queue) > 0:
            msg = self.msg_queue.pop(0)
        self.msg_lock.release()
        return msg

    def is_shutdown(self):
        return self.shutdown

    def run(self):
        raise NotImplementedError(f"{self.__class__.__name__} does not have an implemented run method")


class PriorityCryptoWorker(CryptoWorker):

    def __init__(self, client):
        super().__init__(client)
        self.priority_msg_queue = []
        self.priority_msg_lock = threading.Lock()

    def add_message_to_priority_queue(self, msg):
        self.priority_msg_lock.acquire()
        logger.info(f"PRIORITY: {msg}")
        self.priority_msg_queue.append(msg)
        self.priority_msg_lock.release()

    def get_next_message_from_priority_queue(self):
        msg = None
        self.priority_msg_lock.acquire()
        if len(self.priority_msg_queue) > 0:
            msg = self.priority_msg_queue.pop(0)
        self.priority_msg_lock.release()
        return msg
