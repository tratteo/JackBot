import json
from datetime import datetime
from enum import unique, Enum

from core.bot.logic.wallet_handler import WalletHandler


@unique
class PositionType(str, Enum):
    LONG = "LONG",
    SHORT = "SHORT"


class Position:

    def __init__(self, pos_type: PositionType, open_date: datetime.date, open_price: float, take_profit: float, stop_loss: float, investment: float):
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
        return json.dumps(vars(self), indent = 4)

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

    def open(self, wallet_handler: WalletHandler):
        # print("Order opened: ")
        # print("Symbol: " + self.order_info["symbol"] + "\n executed. Quantity " + self.order_info["executedQty"])
        pass

    def close(self, won: bool, close_price: float, wallet_handler: WalletHandler):
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
