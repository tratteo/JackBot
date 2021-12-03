from abc import abstractmethod, ABC
from typing import List

from core.bot.condition import StrategyCondition
from core.bot.position import PositionType, Position
from core.bot.wallet_handler import WalletHandler, TestWallet


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
        self.__longest_period = 500
        self.wallet_handler = wallet_handler

    @abstractmethod
    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        pass

    @abstractmethod
    def compute_indicators_step(self, frame):
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

            self.compute_indicators_step(frame)

            if len(self.closes) >= self.__longest_period: self.closes = self.closes[-self.__longest_period:]
            if len(self.highs) >= self.__longest_period: self.highs = self.highs[-self.__longest_period:]
            if len(self.lows) >= self.__longest_period: self.lows = self.lows[-self.__longest_period:]
            # Tick all conditions so they can update their internal state
            for c in self.__long_conditions:
                c.tick(frame)

            for c in self.__short_conditions:
                c.tick(frame)

            if len(self.open_positions) < self.max_positions and self.wallet_handler.get_balance() > 0:
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
