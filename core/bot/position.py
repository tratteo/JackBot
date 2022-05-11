from datetime import datetime
from enum import unique, Enum


@unique
class PositionType(str, Enum):
    LONG = "LONG",
    SHORT = "SHORT"


class Position:

    def __init__(self, pos_type: PositionType, open_date: datetime.date, open_price: float, take_profit: float, stop_loss: float, investment: float, ):
        self.result_percentage = 0
        self.pos_type = pos_type
        self.won = False
        self.profit = 0
        self.open_date = open_date
        self.open_price = open_price
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.closed = False
        self.investment = investment

    def __str__(self):
        if self.closed:
            return "Open time: " + "{:2.0f}".format(self.open_date) + \
                   ", investment: " + "{:2.3f}".format(self.investment) + \
                   ", entry price: " + "{:2.3f}".format(self.open_price) + \
                   ", TP: " + "{:2.3f}".format(self.take_profit) + \
                   ", SL: " + "{:2.3f}".format(self.stop_loss) + \
                   ", type: " + str(self.pos_type) + \
                   ", closed: " + str(self.closed) + \
                   ", won: " + str(self.won) + \
                   ", result percentage: " + "{:2.3f}".format(self.result_percentage) + \
                   ", profit: " + "{:2.3f}".format(self.profit)

        else:
            return "Open time: " + "{:2.0f}".format(self.open_date) + \
                   ", investment: " + "{:2.3f}".format(self.investment) + \
                   ", entry price: " + "{:2.3f}".format(self.open_price) + \
                   ", TP: " + "{:2.3f}".format(self.take_profit) + \
                   ", SL: " + "{:2.3f}".format(self.stop_loss) + \
                   ", type: " + str(self.pos_type) + \
                   ", closed: " + str(self.closed)

    def should_close(self, current_price: float) -> [bool, bool]:
        if self.pos_type == PositionType.LONG:
            if current_price >= self.take_profit:
                # win long trade
                return True, True

            elif current_price <= self.stop_loss:
                # lose long trade
                return True, False

        elif self.pos_type == PositionType.SHORT:
            if current_price <= self.take_profit:
                # win short trade
                return True, True

            elif current_price >= self.stop_loss:
                # lose short trade
                return True, False

        return False, False

    def open(self, wallet_handler):
        # print("Order opened: ")
        # print("Symbol: " + self.order_info["symbol"] + "\n executed. Quantity " + self.order_info["executedQty"])
        pass

    def close(self, won: bool, close_price: float, wallet_handler):
        self.won = won
        self.closed = True
        if self.pos_type == PositionType.LONG:
            # pair = pair + "DOWN" + options["second"]
            self.result_percentage = ((close_price / self.open_price) - 1) * 100
        if self.pos_type == PositionType.SHORT:
            # pair = pair + "UP" + options["second"]
            self.result_percentage = ((self.open_price / close_price) - 1) * 100

        self.profit = self.investment * (self.result_percentage / 100)

        # print("Order closed: ")
        # print("Symbol: " + self.order_info["symbol"] + "\n executed. Quantity " + self.order_info["executedQty"])
