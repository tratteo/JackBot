from abc import abstractmethod, ABC


class DataFrame(ABC):
    def __init__(self):
        self.symbol = ''
        self.start_time = 0
        self.close_time = 0
        self.open_price = 0
        self.close_price = 0
        self.high_price = 0
        self.low_price = 0
        self.is_closed = False
