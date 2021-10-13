import datetime
from abc import ABC, abstractmethod
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


    def should_close(self, current_price: float) -> [bool, bool]:
        """Return a tuple[should_close, won]"""
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
            self.result_percentage = ((self.take_profit / self.open_price) - 1) * 100 if won else self.result_percentage = ((self.stop_loss / self.open_price) - 1) * 100
        if self.pos_type == PositionType.SHORT:
            self.result_percentage = ((self.open_price / self.take_profit) - 1) * 100 if won else self.result_percentage = ((self.open_price / self.stop_loss) - 1) * 100
        # TODO send close order


class StrategyCondition:

    def __init__(self, condition, one_time: bool = False, interval_tolerance: int = 0):
        self.one_time = one_time
        self.condition = condition
        self.__satisfied = False
        self.interval_tolerance = interval_tolerance
        self.__tolerance = self.interval_tolerance


    def reset(self):
        self.__tolerance = self.interval_tolerance
        self.__satisfied = False


    @property
    def tolerance(self):
        return self.__tolerance


    @tolerance.setter
    def tolerance(self, new_tolerance):
        self.__tolerance = new_tolerance
        if self.__tolerance < 0: self.__tolerance = 0


    def is_satisfied(self, frame):
        if self.one_time:
            if self.__satisfied and self.__tolerance > 0: return True
        self.__satisfied = self.condition(frame)
        if self.__satisfied and self.one_time: self.__tolerance = self.interval_tolerance
        return self.__satisfied


class Strategy(ABC):

    def __init__(self, max_positions: int):
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


    @abstractmethod
    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        pass


    @abstractmethod
    def get_take_profit(self, open_price: float, position_type: PositionType) -> float:
        pass


    @abstractmethod
    def long_cancel(self, frame) -> bool:
        """The condition for which the long position waiting state is canceled"""
        pass


    @abstractmethod
    def long_necessary(self, frame) -> bool:
        """The condition for which the long position waiting state is opened"""
        pass


    @abstractmethod
    def short_cancel(self, frame) -> bool:
        """The condition for which the short position waiting state is canceled"""
        pass


    @abstractmethod
    def short_necessary(self, frame) -> bool:
        """The condition for which the short position waiting state is opened"""
        pass


    @staticmethod
    def __check_conditions(frame, conditions) -> bool:
        satisfied = True
        for c in conditions:
            satisfied = c.is_satisfied(frame)
        return satisfied


    def update_state(self, frame):
        candle = frame["k"]
        close_price = float(candle["c"])

        # Check for positions that need to be closed
        to_remove = []
        for pos in self.open_positions:
            should_close, won = pos.should_close(close_price)
            if should_close:
                pos.close(won)
                to_remove.append(pos)
                self.closed_positions.append(pos)
        # Remove all the closed positions
        for rem in to_remove:
            self.open_positions.remove(rem)

        if candle["x"]:
            self.closes.append(close_price)
            self.highs.append(float(candle["h"]))
            self.lows.append(float(candle["l"]))

            # If it is possible to open new positions
            if len(self.open_positions) < self.max_positions:
                # If not in long/short alert, check if the necessary condition is met
                if not self.__long_valid:
                    self.__long_valid = self.long_necessary(frame)
                if not self.__short_valid:
                    self.__short_valid = self.short_necessary(frame)

                # Cancel the long/short alert if the cancel sufficient condition is met
                self.__long_valid = not self.long_cancel(frame)
                self.__short_valid = not self.short_cancel(frame)

                # If in long/short alert check for open position condition and open positions
                if self.__long_valid and self.__check_conditions(frame, self.long_conditions):
                    self.__long_valid = False
                    long_pos = Position(PositionType.LONG)
                    long_pos.open(candle["T"], close_price, self.get_take_profit(close_price, PositionType.LONG), self.get_stop_loss(close_price, PositionType.LONG))
                    self.open_positions.append(long_pos)
                    for p in self.long_conditions:
                        p.reset()

                if self.__short_valid and self.__check_conditions(frame, self.short_conditions) and len(self.open_positions) < self.max_positions:
                    self.__short_valid = False
                    short_pos = Position(PositionType.SHORT)
                    short_pos.open(candle["T"], close_price, self.get_take_profit(close_price, PositionType.SHORT), self.get_stop_loss(close_price, PositionType.SHORT))
                    self.open_positions.append(short_pos)
                    for p in self.short_conditions:
                        p.reset()

                for p in self.long_conditions:
                    p.tolerance -= 1
                for p in self.short_conditions:
                    p.tolerance -= 1
            else:
                self.__long_valid = False
                self.__short_valid = False
