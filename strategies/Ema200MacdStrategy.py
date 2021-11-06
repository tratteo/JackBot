from typing import List

import numpy as np
import talib as technical

from core.bot import *
from core.bot.condition import StrategyCondition, PerpetualStrategyCondition, EventStrategyCondition
from core.bot.position import PositionType
from core.bot.strategy import Strategy
from core.bot.wallet_handler import WalletHandler


class Ema200MacdStrategy(Strategy):
    """
    MFI, STOCH, 200 EMA

    Parameters (6):
        risk_reward_ratio\n
        intervals_tolerance\n
        investment_rate\n
        atr_factor\n

    """

    FAST_PERIOD = 12
    SLOW_PERIOD = 26
    SMOOTHING = 9

    MAX_OPEN_POSITIONS_NUMBER = 5

    def __init__(self, wallet_handler: WalletHandler, **strategy_params):
        self.risk_reward_ratio = strategy_params["risk_reward_ratio"]
        self.atr_factor = strategy_params["atr_factor"]
        self.investment_rate = strategy_params["investment_ratio"]
        self.interval_tolerance = strategy_params["interval_tolerance"]
        super().__init__(wallet_handler, self.MAX_OPEN_POSITIONS_NUMBER)

    def compute_indicators(self) -> list[tuple[str, any]]:
        return [('200ema', technical.EMA(np.array(self.closes), timeperiod=200)),
                ("macd", technical.MACD(np.array(self.closes), fastperiod=self.FAST_PERIOD, slowperiod=self.SLOW_PERIOD,
                                        signalperiod=self.SMOOTHING)),
                ("atr", technical.ATR(np.array(self.highs), np.array(self.lows), np.array(self.closes)))

                ]

    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        atr = self.get_indicator("atr")
        if position_type == PositionType.LONG:
            return open_price - (self.atr_factor * atr[-1])
        elif position_type == PositionType.SHORT:
            return open_price + (self.atr_factor * atr[-1])

    def get_take_profit(self, open_price: float, position_type: PositionType) -> float:
        atr = self.get_indicator("atr")
        if position_type == PositionType.LONG:
            return open_price + (self.risk_reward_ratio * self.atr_factor * atr[-1])
        elif position_type == PositionType.SHORT:
            return open_price - (self.risk_reward_ratio * self.atr_factor * atr[-1])

    def get_margin_investment(self) -> float:
        return self.wallet_handler.get_balance() * self.investment_rate

    def get_long_conditions(self) -> List[StrategyCondition]:
        return [PerpetualStrategyCondition(self.long_perpetual_condition),
                EventStrategyCondition(self.long_event_condition, self.interval_tolerance)
                ]

    def get_short_conditions(self) -> List[StrategyCondition]:
        return [PerpetualStrategyCondition(self.short_perpetual_condition),
                EventStrategyCondition(self.short_event_condition, self.interval_tolerance)]

    def long_perpetual_condition(self, frame) -> bool:
        ema200 = self.get_indicator("200ema")
        return self.closes[-1] > ema200[-1]

    def short_perpetual_condition(self, frame) -> bool:
        ema200 = self.get_indicator('200ema')
        return self.closes[-1] < ema200[-1]

    def short_event_condition(self, frame) -> bool:
        macd, signal, hist = self.get_indicator("macd")
        return len(hist) >2 and hist[-2] >= 0 and hist[-1] < 0

    def long_event_condition(self, frame) -> bool:
        macd, signal, hist = self.get_indicator("macd")
        return len(hist) >2 and hist[-2] <= 0 and hist[-1] > 0