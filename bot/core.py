import json
from abc import abstractmethod, ABC
from datetime import datetime
from enum import unique, Enum
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

import config

# region Position
from typing import List, Callable


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
                # Finchè UP e DOWN non sono disponibili

                # if self.pos_type == PositionType.SHORT:
                #     pair = pair + "DOWN" + options["second"]
                # if self.pos_type == PositionType.LONG:
                #    pair = pair + "UP" +  options["second"]

                self.order_info = wallet_handler.client.create_order(
                    symbol = pair,
                    side = 'BUY',
                    type = 'MARKET',
                    quantity = self.investment
                )

        except BinanceAPIException as e:
            print(e)
        except BinanceOrderException as e:
            print(e)

        print("Order opened: ")
        print('symbol: ' + self.order_info['symbol'] + '\nexecutedQty ' + self.order_info['executedQty'])



    def close(self, won: bool, close_price: float, wallet_handler):

        self.won = won
        self.closed = True



        try:
            if isinstance(wallet_handler, BinanceWallet):
                options = wallet_handler.options

                pair = options["first"] + options["second"]
                if self.pos_type == PositionType.LONG:
                    # pair = pair + "DOWN" + options["second"]
                    self.result_percentage = ((close_price / self.open_price) - 1) * 100
                if self.pos_type == PositionType.SHORT:
                    # pair = pair + "UP" + options["second"]
                    self.result_percentage = ((self.open_price / close_price) - 1) * 100

                pair = options["first"] + options["second"]
                self.order_info = wallet_handler.client.create_order(
                    symbol=pair,
                    side='SELL',
                    type='MARKET',
                    quantity=self.investment
                )

        except BinanceAPIException as e:
            print(e)
        except BinanceOrderException as e:
            print(e)

        self.profit = self.investment * (self.result_percentage / 100)

        print("Order closed: ")
        print('symbol: ' + self.order_info['symbol'] + '\nexecutedQty ' + self.order_info['executedQty'])

    def get_order_info(self):
        print(self.order_info)


# endregion

# region Condition


class StrategyCondition(ABC):

    def __init__(self):
        self.satisfied = False

    @abstractmethod
    def tick(self, frame):
        pass

    @abstractmethod
    def reset(self):
        self.satisfied = False
        pass


class PerpetualStrategyCondition(StrategyCondition):

    def __init__(self, condition_delegate: Callable[[dict], bool]):
        super().__init__()
        self.__condition_delegate = condition_delegate

    def tick(self, frame):
        self.satisfied = self.__condition_delegate(frame)
        pass

    def reset(self):
        super().reset()
        pass


class EventStrategyCondition(StrategyCondition):

    def __init__(self, condition_delegate: Callable[[dict], bool], tolerance_duration: int):
        super().__init__()
        self.__condition_delegate = condition_delegate
        self.__tolerance_duration = tolerance_duration
        self.__current_tolerance = 0

    def tick(self, frame):
        if not self.satisfied:
            self.satisfied = self.__condition_delegate(frame)
            if self.satisfied: self.__current_tolerance = 0
        else:
            self.satisfied = self.__current_tolerance <= self.__tolerance_duration

        if self.satisfied:
            self.__current_tolerance += 1

    def reset(self):
        super().reset()
        self.__current_tolerance = 0
        pass


class BoundedStrategyCondition(StrategyCondition):

    def __init__(self, valid_condition_delegate: Callable[[dict], bool], invalid_condition_delegate: Callable[[dict], bool], duration_tolerance: int = 0):
        super().__init__()
        self.__valid_condition_delegate = valid_condition_delegate
        self.__invalid_condition_delegate = invalid_condition_delegate
        self.__duration_tolerance = duration_tolerance
        self.__current_tolerance = 0

    def tick(self, frame):
        if not self.satisfied:
            self.satisfied = self.__valid_condition_delegate(frame)
            if self.satisfied: self.__current_tolerance = 0
        else:
            self.satisfied = not self.__invalid_condition_delegate(frame) and self.__current_tolerance < self.__duration_tolerance

        if self.satisfied:
            self.__current_tolerance += 1

    def reset(self):
        super().reset()
        self.__current_tolerance = 0
        pass


# endregion

# region WalletHandlers

class WalletHandler(ABC):

    @abstractmethod
    def get_asset_balance(self):
        pass

    def get_second_balance(self):
        pass


class BinanceWallet(WalletHandler):

    def __init__(self, options, api_key, api_secret):
        self.options = options
        self.client = Client(api_key, api_secret)
        self.client.API_URL = 'https://testnet.binance.vision/api'

    def get_asset_balance(self):
        return float(self.client.get_asset_balance(asset=self.options["first"])["free"])

    def get_second_balance(self):
        return float(self.client.get_asset_balance(asset=self.options["second"])["free"])



class TestWallet(WalletHandler):

    @classmethod
    def factory(cls, initial_balance: float = 1000):
        return TestWallet(initial_balance)

    def __init__(self, initial_balance: float):
        self.__balance = initial_balance

    @property
    def balance(self):
        return self.__balance

    def get_balance(self):
        return self.balance

    @balance.setter
    def balance(self, value: float):
        self.__balance = value


# endregion

# region Strategy

class Strategy(ABC):

    def __init__(self, wallet_handler: WalletHandler, max_positions: int):
        self.max_positions = max_positions
        self.open_positions = []
        self.closed_positions = []
        self.closes = []
        self.highs = []
        self.lows = []
        self.__long_conditions = self.get_long_conditions()
        self.__short_conditions = self.get_short_conditions()
        self.__longest_period = 150
        self.wallet_handler = wallet_handler
        self.__indicators = dict()

    @abstractmethod
    def compute_indicators(self) -> list[tuple[str, any]]:
        pass

    @abstractmethod
    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        pass

    @abstractmethod
    def get_take_profit(self, open_price: float, position_type: PositionType) -> float:
        pass

    @abstractmethod
    def get_margin_investment(self) -> float:
        pass

    @abstractmethod
    def get_long_conditions(self) -> List[StrategyCondition]:
        pass

    @abstractmethod
    def get_short_conditions(self) -> List[StrategyCondition]:
        pass

    @staticmethod
    def __check_conditions(conditions: List[StrategyCondition]) -> bool:
        for c in conditions:
            if not c.satisfied:
                return False
        return True

    def get_indicator(self, key: str):
        return self.__indicators.get(key)

    @staticmethod
    def __reset_conditions(conditions):
        for c in conditions:
            c.reset()

    def update_state(self, frame, verbose: bool = False):
        candle = frame["k"]
        close_price = float(candle["c"])

        to_remove = []
        for pos in self.open_positions:
            should_close, won = pos.should_close(close_price)
            if should_close:
                pos.close(won, close_price, self.wallet_handler)
                if isinstance(self.wallet_handler, TestWallet):
                    self.wallet_handler.balance += pos.profit + pos.investment
                to_remove.append(pos)
                self.closed_positions.append(pos)
                if verbose: print("Closed position: " + str(pos))
        # Remove all the closed positions
        for rem in to_remove:
            self.open_positions.remove(rem)

        if candle["x"]:
            self.closes.append(close_price)
            self.highs.append(float(candle["h"]))
            self.lows.append(float(candle["l"]))

            for p in self.compute_indicators():
                self.__indicators[p[0]] = p[1]

            if len(self.closes) >= self.__longest_period: self.closes = self.closes[-self.__longest_period:]
            if len(self.highs) >= self.__longest_period: self.highs = self.highs[-self.__longest_period:]
            if len(self.lows) >= self.__longest_period: self.lows = self.lows[-self.__longest_period:]
            # Tick all conditions so they can update their internal state
            for c in self.__long_conditions:
                c.tick(frame)

            for c in self.__short_conditions:
                c.tick(frame)

            if len(self.open_positions) < self.max_positions and self.wallet_handler.get_asset_balance() > 0:
                if self.__check_conditions(self.__long_conditions):
                    investment = self.get_margin_investment()
                    pos = Position(PositionType.LONG, candle["t"], close_price, self.get_take_profit(close_price, PositionType.LONG), self.get_stop_loss(close_price, PositionType.LONG), investment)
                    if isinstance(self.wallet_handler, TestWallet):
                        self.wallet_handler.balance -= investment
                    pos.open(self.wallet_handler)
                    self.open_positions.append(pos)
                    if verbose: print("\nOpened position: " + str(pos))
                    self.__reset_conditions(self.__long_conditions)

                if self.__check_conditions(self.__short_conditions):
                    investment = self.get_margin_investment()
                    pos = Position(PositionType.SHORT, candle["t"], close_price, self.get_take_profit(close_price, PositionType.SHORT), self.get_stop_loss(close_price, PositionType.SHORT), investment)
                    if isinstance(self.wallet_handler, TestWallet):
                        self.wallet_handler.balance -= investment
                    pos.open(self.wallet_handler)
                    self.open_positions.append(pos)
                    if verbose: print("\nOpened position: " + str(pos))
                    self.__reset_conditions(self.__short_conditions)

# endregion
