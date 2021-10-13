import datetime
from abc import ABC, abstractmethod
from enum import Enum, unique


@unique
class PositionStatus(Enum):
    OPEN = 0,
    CLOSED = 1


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
        self.status = PositionStatus.OPEN
        self.won = False

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

    def open(self, open_date: datetime.date, open_price: float, take_profit: float, stop_loss: float):
        self.open_date = open_date
        self.open_price = open_price
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.status = PositionStatus.OPEN
        # TODO send open order
        # TODO set limit order for stop loss and take profit

    def close(self, won: bool):
        self.won = won
        self.status = PositionStatus.CLOSED
        if self.pos_type == PositionType.LONG:
            self.result_percentage = ((self.take_profit / self.open_price) - 1) * 100 if won else self.result_percentage = ((self.stop_loss / self.open_price) - 1) * 100
        if self.pos_type == PositionType.SHORT:
            self.result_percentage = ((self.open_price / self.take_profit) - 1) * 100 if won else self.result_percentage = ((self.open_price / self.stop_loss) - 1) * 100
        # TODO send close order


class Strategy(ABC):

    def __init__(self, max_positions):
        self.max_positions = max_positions
        self.__long_alert = False
        self.__short_alert = False
        self.open_positions = []
        self.closed_positions = []
        self.closes = []
        self.highs = []
        self.lows = []

    @abstractmethod
    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        pass

    @abstractmethod
    def get_take_profit(self, open_price: float, position_type: PositionType) -> float:
        pass

    @abstractmethod
    def long_cancel_sufficient(self, message) -> bool:
        pass

    @abstractmethod
    def long_allow_necessary(self, message) -> bool:
        pass

    @abstractmethod
    def open_long_condition(self, message) -> bool:
        pass

    @abstractmethod
    def short_cancel_sufficient(self, message) -> bool:
        pass

    @abstractmethod
    def short_allow_necessary(self, message) -> bool:
        pass

    @abstractmethod
    def open_short_condition(self, message) -> bool:
        pass

    def update_state(self, frame):
        candle = frame["k"]
        is_candle_closed = candle["x"]
        close_price = float(candle["c"])
        high_price = float(candle["h"])
        low_price = float(candle["l"])

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

        if is_candle_closed:
            self.closes.append(close_price)
            self.highs.append(high_price)
            self.lows.append(low_price)

            # If it is possible to open new positions
            if len(self.open_positions) < self.max_positions:
                # If not in long/short alert, check if the necessary condition is met
                if not self.__long_alert:
                    self.__long_alert = self.long_allow_necessary(frame)
                if not self.__short_alert:
                    self.__short_alert = self.short_allow_necessary(frame)

                # Cancel the long/short alert if the cancel sufficient condition is met
                self.__long_alert = not self.long_cancel_sufficient(frame)
                self.__short_alert = not self.short_cancel_sufficient(frame)

                # If in long/short alert check for open position condition and open positions
                if self.__long_alert and self.open_long_condition(frame) and len(self.open_positions) < self.max_positions:
                    self.__long_alert = False
                    long_pos = Position(PositionType.LONG)
                    long_pos.open(candle["T"], close_price, self.get_take_profit(close_price, PositionType.LONG), self.get_stop_loss(close_price, PositionType.LONG))
                    self.open_positions.append(long_pos)

                if self.__short_alert and self.open_short_condition(frame) and len(self.open_positions) < self.max_positions:
                    self.__short_alert = False
                    short_pos = Position(PositionType.SHORT)
                    short_pos.open(candle["T"], close_price, self.get_take_profit(close_price, PositionType.SHORT), self.get_stop_loss(close_price, PositionType.SHORT))
                    self.open_positions.append(short_pos)
