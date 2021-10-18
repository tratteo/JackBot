import json
from abc import abstractmethod, ABC
from datetime import datetime
from enum import unique, Enum


# region Position


@unique
class PositionType(Enum):
    LONG = 0,
    SHORT = 1


class Position:

    def __init__(self, pos_type, handle_orders: bool = True):
        self.open_date = None
        self.open_price = 0
        self.result_percentage = 0
        self.take_profit = 0
        self.stop_loss = 0
        self.pos_type = pos_type
        self.closed = False
        self.won = False
        self.investment = 0
        self.profit = 0
        self.handle_orders = handle_orders


    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


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


    def open(self, open_date: datetime.date, open_price: float, take_profit: float, stop_loss: float, investment: float):
        self.open_date = open_date
        self.open_price = open_price
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.closed = False
        self.investment = investment
        if self.handle_orders:
            # TODO send open order, stop loss and take profit
            pass


    def close(self, won: bool, close_price: float):
        self.won = won
        self.closed = True
        if self.pos_type == PositionType.LONG:
            if won:
                self.result_percentage = ((close_price / self.open_price) - 1) * 100
            else:
                self.result_percentage = ((close_price / self.open_price) - 1) * 100
        if self.pos_type == PositionType.SHORT:
            if won:
                self.result_percentage = ((self.open_price / close_price) - 1) * 100
            else:
                self.result_percentage = ((self.open_price / close_price) - 1) * 100
        self.profit = self.investment * (self.result_percentage / 100)


# endregion

# region Condition


class StrategyCondition(ABC):

    def __init__(self):
        self.satisfied = False


    @abstractmethod
    def tick(self, frame):
        pass


class PerpetualStrategyCondition(StrategyCondition):

    def __init__(self, condition):
        super().__init__()
        self.condition = condition


    def tick(self, frame):
        self.satisfied = self.condition(frame)
        pass


class EventStrategyCondition(StrategyCondition):

    def __init__(self, condition, tolerance_duration: int):
        super().__init__()
        self.condition = condition
        self.tolerance_duration = tolerance_duration
        self.current_tolerance = 0


    def tick(self, frame):
        if not self.satisfied:
            self.satisfied = self.condition(frame)
            if self.satisfied: self.current_tolerance = 0
        else:
            self.satisfied = self.current_tolerance <= self.tolerance_duration

        if self.satisfied:
            self.current_tolerance += 1


class DoubledStrategyCondition(StrategyCondition):

    def __init__(self, valid_condition, invalid_condition, duration_tolerance: int = 0):
        super().__init__()
        self.valid_condition = valid_condition
        self.invalid_condition = invalid_condition
        self.duration_tolerance = duration_tolerance
        self.current_tolerance = 0


    def tick(self, frame):
        if not self.satisfied:
            self.satisfied = self.valid_condition(frame)
            if self.satisfied: self.current_tolerance = 0
        else:
            self.satisfied = not self.invalid_condition(frame) and self.current_tolerance < self.duration_tolerance

        if self.satisfied:
            self.current_tolerance += 1


# endregion

# region WalletHandler

class WalletHandler:

    def __init__(self, change_balance_delegate, get_balance_delegate):
        self.__change_balance_delegate = change_balance_delegate
        self.__get_balance_delegate = get_balance_delegate


    def change_balance(self, amount):
        self.__change_balance_delegate(amount)


    def get_balance(self):
        return self.__get_balance_delegate()


# endregion

# region Strategy


class Strategy(ABC):

    def __init__(self, wallet_handler: WalletHandler, max_positions: int, handle_positions: bool = False, longest_period: int = 200):
        self.max_positions = max_positions
        self.__long_valid = False
        self.__short_valid = False
        self.open_positions = []
        self.closed_positions = []
        self.closes = []
        self.highs = []
        self.lows = []
        self.long_conditions = []
        self.short_conditions = []
        self.handle_positions = handle_positions
        self.wallet_handler = wallet_handler
        self.longest_period = longest_period


    @abstractmethod
    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        pass


    @abstractmethod
    def get_take_profit(self, open_price: float, position_type: PositionType) -> float:
        pass


    @abstractmethod
    def get_margin_investment(self):
        pass


    @staticmethod
    def __check_conditions(conditions) -> bool:
        for c in conditions:
            if not c.satisfied:
                return False
        return True


    def update_state(self, frame, verbose: bool = False):
        candle = frame["k"]
        close_price = float(candle["c"])

        if self.handle_positions:
            # Check for positions that need to be closed
            to_remove = []
            for pos in self.open_positions:
                should_close, won = pos.should_close(close_price)
                if should_close:
                    pos.close(won, close_price)
                    self.wallet_handler.change_balance(pos.profit + pos.investment)
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

            if len(self.closes) >= self.longest_period: self.closes = self.closes[-self.longest_period:]
            if len(self.highs) >= self.longest_period: self.highs = self.highs[-self.longest_period:]
            if len(self.lows) >= self.longest_period: self.lows = self.lows[-self.longest_period:]
            # Tick all conditions so they can update their internal state
            for c in self.long_conditions:
                c.tick(frame)

            for c in self.short_conditions:
                c.tick(frame)

            if len(self.open_positions) < self.max_positions and self.wallet_handler.get_balance() > 0:
                if self.__check_conditions(self.long_conditions):
                    pos = Position(PositionType.LONG, not self.handle_positions)
                    investment = self.get_margin_investment()
                    self.wallet_handler.change_balance(-investment)
                    pos.open(candle["t"], close_price, self.get_take_profit(close_price, PositionType.LONG), self.get_stop_loss(close_price, PositionType.LONG), investment)
                    self.open_positions.append(pos)
                    if verbose: print("\nOpened position: " + str(pos))

                if self.__check_conditions(self.short_conditions):
                    pos = Position(PositionType.SHORT, not self.handle_positions)
                    investment = self.get_margin_investment()
                    self.wallet_handler.change_balance(-investment)
                    pos.open(candle["t"], close_price, self.get_take_profit(close_price, PositionType.SHORT), self.get_stop_loss(close_price, PositionType.SHORT), investment)
                    self.open_positions.append(pos)
                    if verbose: print("\nOpened position: " + str(pos))


# endregion
