from abc import ABC


class DataFrame(ABC):
    def __init__(self):
        self.symbol = ''
        self.start_time: int = 0
        self.close_time: int = 0
        self.open_price: float = 0
        self.close_price: float = 0
        self.high_price: float = 0
        self.low_price: float = 0
        self.is_closed: bool = False
