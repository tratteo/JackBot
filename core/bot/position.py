import json
import os
import datetime
from abc import ABC, abstractmethod
from enum import unique, Enum
import config
from binance.enums import *
from kucoin_futures.client import User

from binance.exceptions import BinanceAPIException, BinanceOrderException

# region Position
from core.bot.wallet_handler import BinanceWallet
from core.bot.wallet_handler import KucoinWallet_future


@unique
class PositionType(Enum):
    LONG = 0,
    SHORT = 1


@unique
class OrderType(Enum):
    LIMIT = 0,
    MARKET = 1


@unique
class Env(Enum):
    Kucoin = 0,
    Binace = 1

class Position(ABC):

    def __init__(self, currency: str, pos_type: PositionType, ord_type: OrderType, open_date: datetime.date,
                 open_price: float, take_profit: float,
                 stop_loss: float, investment: float, wallet_handler):
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
        self.TPSL_info = None
        self.wallet_handler = wallet_handler
        self.currency = currency
        self.ord_type = ord_type

    def should_close(self, current_price: float) -> [bool, bool]:
        """Return if should close, win/loss"""

        if self.pos_type == PositionType.LONG:
            if current_price >= self.take_profit:
                self.closed = True
                self.won = True

            elif current_price <= self.stop_loss:
                self.closed = True
                self.won = False

        elif self.pos_type == PositionType.SHORT:
            if current_price <= self.take_profit:
                self.closed = True
                self.won = True

            elif current_price >= self.stop_loss:
                self.closed = True
                self.won = False

        return self.closed


    def __str__(self):
        if self.closed:
            print(self.open_date)
            return "Open time: " + str(self.open_date) + \
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
            return "Open time: " + str(self.open_date) + \
                   ", investment: " + "{:2.3f}".format(self.investment) + \
                   ", entry price: " + "{:2.3f}".format(self.open_price) + \
                   ", TP: " + "{:2.3f}".format(self.take_profit) + \
                   ", SL: " + "{:2.3f}".format(self.stop_loss) + \
                   ", type: " + str(self.pos_type) + \
                   ", closed: " + str(self.closed)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    @abstractmethod
    def close(self, won: bool, close_price: float, wallet_handler):
        pass


class KucoinPosition(Position):

    def __init__(self, currency: str, pos_type: PositionType, ord_type: OrderType, open_date: datetime.date,
                 open_price: float, take_profit: float, stop_loss: float, investment: float, leverage: float,  wallet_handler):

        super().__init__(currency, pos_type, ord_type, open_date, open_price, take_profit, stop_loss, investment,
                         wallet_handler)
        side = 'buy'
        if pos_type == PositionType.SHORT:
            side = 'sell'

        if isinstance(wallet_handler, KucoinWallet_future):

            if self.ord_type == OrderType.MARKET:
                self.order_info = wallet_handler.trade.create_market_order(currency, side, str(leverage), size=str(investment))
                self.TPSL_info = wallet_handler.trade.TPSL(currency, side, str(leverage), str(investment), take_profit, stop_loss)

            elif self.ord_type == OrderType.LIMIT:
                # SL not implemented
                self.order_info = wallet_handler.trade.create_market_order(currency, side, str(leverage), size=str(investment), price=str(open_price))

        else:
            print("Not a Kucoin futures wallet")

    def close(self, won: bool, close_price: float, wallet_handler):
        pass




class BinancePosition(Position):

    def __init__(self, currency: str, pos_type: PositionType, ord_type: OrderType, open_date: datetime.date,
                 open_price: float, take_profit: float, stop_loss: float, investment: float, wallet_handler):

        super().__init__(currency, pos_type, ord_type, open_date, open_price, take_profit, stop_loss, investment,
                         wallet_handler)
        try:
            if isinstance(wallet_handler, BinanceWallet):

                if self.ord_type == OrderType.MARKET:
                    self.order_info = wallet_handler.client.order_market_buy(
                        symbol=self.currency,
                        quantity=self.investment)

                elif self.ord_type == OrderType.LIMIT:
                    self.order_info = wallet_handler.client.order_limit_buy(
                        symbol=self.currency,
                        quantity=self.investment,
                        price=self.open_price)
            else:
                print("Not a BinanceWallet")

        except BinanceAPIException as e:
            print(e)
        except BinanceOrderException as e:
            print(e)

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

                self.order_info = wallet_handler.client.order_market_sell(
                    symbol=self.currency,
                    quantity=self.investment
                )

            except BinanceAPIException as e:
                print(e)
            except BinanceOrderException as e:
                print(e)

        else:
            print("Not a BinanceWallet")

        self.profit = self.investment * (self.result_percentage / 100)

    def get_order_info(self):
        print(self.order_info)


if __name__ == "__main__":

    wallet = KucoinWallet_future(os.environ.get('FKUCOIN_KEY'), os.environ.get('FKUCOIN_SECRET'), os.environ.get('FKUCOIN_PASS'))
    pos = KucoinPosition('XBTUSDTM', PositionType.LONG, OrderType.MARKET, datetime.datetime.now(), open_price=0, take_profit=50000, stop_loss=40000, leverage=10, investment=1, wallet_handler=wallet)

    print(pos.order_info)
    print(pos.TPSL_info)




