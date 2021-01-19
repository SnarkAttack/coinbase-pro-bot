import threading

class ThreadMessage(threading.Thread):

    def __init__(self, sender, recipient):
        self.sender = sender
        self.recipient = recipient

    def __repr__(self):
        return f"({self.sender} --> {self.recipient})"