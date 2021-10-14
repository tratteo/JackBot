from abc import abstractmethod, ABC

from Core.Position import *


class Strategy(ABC):
    STOCH_OVERBOUGHT = 80
    STOCH_OVERSOLD = 20
    STOCH_FAST_K = 14
    STOCH_SLOW_K = 1
    STOCH_SLOW_D = 3
    RISK_REWARD = 1.5
    ATR_FACTOR = 1.5
    RSI_PERIOD = 14
    MAX_OPEN_POSITIONS_NUMBER = 2
    INTERVALS_TOLERANCE_NUMBER = 5


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


    def __check_conditions(self, frame, conditions) -> bool:
        for c in conditions:
            if not c.satisfied:
                return False
        return True


    def update_state(self, frame):
        candle = frame["k"]
        close_price = float(candle["c"])

        # # Check for positions that need to be closed
        # to_remove = []
        # for pos in self.open_positions:
        #     should_close, won = pos.should_close(close_price)
        #     if should_close:
        #         pos.close(won)
        #         to_remove.append(pos)
        #         self.closed_positions.append(pos)
        # # Remove all the closed positions
        # for rem in to_remove:
        #     self.open_positions.remove(rem)

        if candle["x"]:
            self.closes.append(close_price)
            self.highs.append(float(candle["h"]))
            self.lows.append(float(candle["l"]))

            # Tick all conditions so they can update their internal state
            for c in self.long_conditions:
                c.tick(frame)

            for c in self.short_conditions:
                c.tick(frame)

            # If all the conditions are met, enter long
            if self.__check_conditions(frame, self.long_conditions):
                print("\nShould enter LONG at: " + str(candle["t"]))
                pos = Position(PositionType.LONG)
                pos.open(candle["t"], close_price, self.get_take_profit(close_price, PositionType.LONG), self.get_stop_loss(close_price, PositionType.LONG))
                print("Pos: " + str(pos))

            if self.__check_conditions(frame, self.short_conditions):
                print("\nShould enter SHORT at: " + str(candle["t"]))
                pos = Position(PositionType.SHORT)
                pos.open(candle["t"], close_price, self.get_take_profit(close_price, PositionType.SHORT), self.get_stop_loss(close_price, PositionType.SHORT))
                print("Pos: " + str(pos))
        # If it is possible to open new positions
        # if len(self.open_positions) < self.max_positions:
        #     # If not in long/short alert, check if the necessary condition is met
        #     if not self.__long_valid:
        #         self.__long_valid = self.long_necessary(frame)
        #     if not self.__short_valid:
        #         self.__short_valid = self.short_necessary(frame)
        #
        #     # Cancel the long/short alert if the cancel sufficient condition is met
        #     self.__long_valid = not self.long_cancel(frame)
        #     self.__short_valid = not self.short_cancel(frame)
        #
        #     # If in long/short alert check for open position condition and open positions
        #     if self.__long_valid and self.__check_conditions(frame, self.long_conditions):
        #         self.__long_valid = False
        #         long_pos = Position(PositionType.LONG)
        #         long_pos.open(candle["t"], close_price, self.get_take_profit(close_price, PositionType.LONG), self.get_stop_loss(close_price, PositionType.LONG))
        #         self.open_positions.append(long_pos)
        #
        #         print("Opened: " + str(long_pos))
        #         for p in self.long_conditions:
        #             p.reset()
        #
        #     # if self.__short_valid and self.__check_conditions(frame, self.short_conditions) and len(self.open_positions) < self.max_positions:
        #     #     self.__short_valid = False
        #     #     short_pos = Position(PositionType.SHORT)
        #     #     short_pos.open(candle["T"], close_price, self.get_take_profit(close_price, PositionType.SHORT), self.get_stop_loss(close_price, PositionType.SHORT))
        #     #     self.open_positions.append(short_pos)
        #     #     print("Opened: " + str(short_pos))
        #     #     for p in self.short_conditions:
        #     #         p.reset()
        #
        #     for p in self.long_conditions:
        #         p.tolerance -= 1
        #     for p in self.short_conditions:
        #         p.tolerance -= 1
        # else:
        #     self.__long_valid = False
        #     self.__short_valid = False
