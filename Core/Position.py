from datetime import datetime
from enum import Enum, unique


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
        self.closed = False
        self.won = False


    def __str__(self):
        return "Open: " + str(self.open_date) + \
               ", o: " + str(self.open_price) + \
               ", r: " + str(self.result_percentage) + \
               ", tp: " + str(self.take_profit) + \
               ", sl: " + str(self.stop_loss) + \
               ", type: " + str(self.pos_type) + \
               ", closed: " + str(self.closed) + \
               ", won: " + str(self.won)


    def should_close(self, current_price: float) -> [bool, bool]:
        """
        Return
        a
        tuple[should_close, won]
        """
        if self.pos_type == PositionType.LONG:
            if current_price >= self.take_profit:
                # win long trade
                return True, True
                pass
            elif current_price <= self.stop_loss:
                # lose long trade
                return True, False
                pass
        elif self.pos_type == PositionType.SHORT:
            if current_price <= self.take_profit:
                # win short trade
                return True, True
                pass
            elif current_price >= self.stop_loss:
                # lose short trade
                return True, False
                pass
        return False, False


    def open(self, open_date: datetime.date, open_price: float, take_profit: float, stop_loss: float):
        self.open_date = open_date
        self.open_price = open_price
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.closed = False
        # TODO send open order
        # TODO set limit order for stop loss and take profit


    def close(self, won: bool):
        self.won = won
        self.closed = True
        if self.pos_type == PositionType.LONG:
            if won:
                self.result_percentage = ((self.take_profit / self.open_price) - 1) * 100
            else:
                self.result_percentage = ((self.stop_loss / self.open_price) - 1) * 100
        if self.pos_type == PositionType.SHORT:
            if won:
                self.result_percentage = ((self.open_price / self.take_profit) - 1) * 100
            else:
                self.result_percentage = ((self.open_price / self.stop_loss) - 1) * 100
        # TODO send close order
