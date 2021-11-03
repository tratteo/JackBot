import json
from datetime import datetime
from enum import unique, Enum

from binance.exceptions import BinanceAPIException, BinanceOrderException

# region Position
from core.bot.wallet_handler import BinanceWallet


@unique
class PositionType(Enum):
    LONG = 0,
    SHORT = 1


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
        self.order_info = None

    def to_json(self):
        return json.dumps(self, default = lambda o: o.__dict__,
                          sort_keys = True, indent = 4)

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

    def open(self, wallet_handler):
        try:
            if isinstance(wallet_handler, BinanceWallet):
                options = wallet_handler.options

                pair = options["first"] + options["second"]
                # Until UP e DOWN are not available

                # if self.pos_type == PositionType.SHORT:
                #     pair = pair + "DOWN" + options["second"]
                # if self.pos_type == PositionType.LONG:
                #    pair = pair + "UP" +  options["second"]

                self.order_info = wallet_handler.client.create_order(
                    symbol = pair,
                    side = "BUY",
                    type = "MARKET",
                    quantity = self.investment)

        except BinanceAPIException as e:
            print(e)
        except BinanceOrderException as e:
            print(e)

        # print("Order opened: ")
        # print("Symbol: " + self.order_info["symbol"] + "\n executed. Quantity " + self.order_info["executedQty"])

    def close(self, won: bool, close_price: float, wallet_handler):
        self.won = won
        self.closed = True
        if self.pos_type == PositionType.LONG:
            # pair = pair + "DOWN" + options["second"]
            self.result_percentage = ((close_price / self.open_price) - 1) * 100
        if self.pos_type == PositionType.SHORT:
            # pair = pair + "UP" + options["second"]
            self.result_percentage = ((self.open_price / close_price) - 1) * 100
        if isinstance(wallet_handler, BinanceWallet):
            try:
                options = wallet_handler.options

                pair = options["first"] + options["second"]
                self.order_info = wallet_handler.client.create_order(
                    symbol = pair,
                    side = "SELL",
                    type = "MARKET",
                    quantity = self.investment
                )

            except BinanceAPIException as e:
                print(e)
            except BinanceOrderException as e:
                print(e)

        self.profit = self.investment * (self.result_percentage / 100)

        # print("Order closed: ")
        # print("Symbol: " + self.order_info["symbol"] + "\n executed. Quantity " + self.order_info["executedQty"])

    def get_order_info(self):
        print(self.order_info)
