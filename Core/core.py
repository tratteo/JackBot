from abc import ABC, abstractmethod
from enum import Enum, unique


@unique
class Status(Enum):
    OPEN = 0,
    WON = 1,
    LOST = 2,
    WAITING = 3


@unique
class PositionType(Enum):
    LONG = 0,
    SHORT = 1


class Position:

    def __init__(self, pos_type):
        self.open_date = None
        self.open_price = 0
        self.result_percentage = 0
        self.take_profit = 0
        self.stop_loss = 0
        self.pos_type = pos_type
        self.status = Status.WAITING

    def should_close(self, current_price):
        """Returns whether the position should be closed"""
        """:rtype bool"""
        if self.pos_type == PositionType.LONG:
            if current_price >= self.take_profit:
                # win long trade
                return True, Status.WON
                pass
            elif current_price <= self.stop_loss:
                # lose long trade
                return True, Status.WON
                pass
        elif self.pos_type == PositionType.SHORT:
            if current_price <= self.take_profit:
                # win short trade
                return True, Status.WON
                pass
            elif current_price >= self.stop_loss:
                # lose short trade
                return True, Status.WON
                pass
        return False, Status.LOST

    def open(self, open_date, open_price, take_profit, stop_loss):
        self.open_date = open_date
        self.open_price = open_price
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.status = Status.OPEN

    def close(self, status):
        self.status = status
        # TODO calculate: result_percentage


class Strategy(ABC):

    def __init__(self, max_positions):
        self.max_positions = max_positions
        self.positions = []
        self.closes = []
        self.highs = []
        self.lows = []

    @abstractmethod
    def get_stop_loss(self, open_price):
        """:rtype: float"""
        pass

    @abstractmethod
    def get_take_profit(self, open_price):
        """:rtype: float"""
        pass

    @abstractmethod
    def can_long(self):
        pass

    @abstractmethod
    def can_short(self):
        pass

    def update_state(self, frame):
        candle = frame["k"]
        is_closed = candle["x"]
        close = float(candle["c"])
        high = float(candle["h"])
        low = float(candle["l"])

        for pos in self.positions:
            should, close_type = pos.should_close(close)
            if should:
                pos.close(close_type)
                # TODO send close order

        if is_closed:
            self.closes.append(close)
            self.highs.append(high)
            self.lows.append(low)
            if len(self.positions) < self.max_positions:
                # TODO check for positions opening
                pass

        pass
