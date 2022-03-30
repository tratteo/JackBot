import datetime
import os
import time
from abc import abstractmethod, ABC
from typing import List
import time
from CexLib.Kucoin.KucoinData import KucoinData
from core.bot.condition import StrategyCondition

from core.bot.middle_ware import DataFrame

from core.bot.position import PositionType, Position, OrderType, KucoinPosition

from core.bot.wallet_handler import WalletHandler, TestWallet


class Strategy(ABC):

    #condizioni in base alle quali entriamo o usciamo da una posizione

    def __init__(self, wallet_handler: WalletHandler, max_positions: int):
        self.max_positions = max_positions
        self.open_positions = []
        self.closed_positions = []
        self.__long_conditions = self.get_long_conditions()
        self.__short_conditions = self.get_short_conditions()
        self.__longest_period = 500
        self.wallet_handler = wallet_handler
        self.balance_trend = []
        self.data = KucoinData(os.environ.get('FK_KEY'), os.environ.get('FK_SECRET'), os.environ.get('FK_PASS'))

    @abstractmethod
    def get_stop_loss(self, symbol: str, open_price: float, position_type: PositionType) -> float:
        pass

    @abstractmethod

    def compute_indicators_step(self, symbol: str, frame: DataFrame):
        pass

    @abstractmethod
    def get_take_profit(self, symbol: str, open_price: float, position_type: PositionType) -> float:
        pass

    @abstractmethod
    def get_margin_investment(self) -> float:
        pass

    @abstractmethod
    def get_leverage(self) -> float:
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


    def update_state(self, frame: DataFrame, verbose: bool = False):

        to_remove = []
        for pos in self.open_positions:
            closed = pos.should_close()
            if closed:
                self.closed_positions.append(pos)
                to_remove.append(pos)

        for rem in to_remove:
            self.open_positions.remove(rem)


        market_price = self.data.get_current_mark_price(frame.symbol)
        self.compute_indicators_step(frame)

        for c in self.__long_conditions:
            c.tick(frame)

        for c in self.__short_conditions:
            c.tick(frame)

        if len(self.open_positions) < self.max_positions and self.wallet_handler.get_balance() > 0:
            if self.__check_conditions(self.__long_conditions):
                investment = self.get_margin_investment()

                pos = KucoinPosition(frame.symbol, PositionType.LONG, OrderType.MARKET, datetime.datetime.utcnow(),
                                     market_price, self.get_take_profit(frame.symbol, market_price, PositionType.LONG),
                                     self.get_stop_loss(market_price, PositionType.LONG),
                                     self.get_margin_investment(),
                                     self.get_leverage(), self.wallet_handler)
                if isinstance(self.wallet_handler, TestWallet):
                    self.wallet_handler.balance -= investment

                self.open_positions.append(pos)
                if verbose: print("\nOpened position: " + str(pos))
                self.__reset_conditions(self.__long_conditions)  # resetta le condizioni, in caso che siano perpetue

            if self.__check_conditions(self.__short_conditions):
                investment = self.get_margin_investment()

                pos = KucoinPosition(frame.symbol, PositionType.SHORT, OrderType.MARKET, datetime.datetime.utcnow(),
                                     market_price, self.get_take_profit(frame.symbol, market_price, PositionType.LONG),
                                     self.get_stop_loss(market_price, PositionType.LONG),
                                     self.get_margin_investment(),
                                     self.get_leverage(), self.wallet_handler)
                if isinstance(self.wallet_handler, TestWallet):
                    self.wallet_handler.balance -= investment

                self.open_positions.append(pos)
                if verbose: print("\nOpened position: " + str(pos))
                self.__reset_conditions(self.__long_conditions)  # resetta le condizioni, in caso che siano perpetue
