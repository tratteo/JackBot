import numpy as np

from core.bot.condition import PerpetualStrategyCondition, EventStrategyCondition
from core.bot.strategy import *
from indicators.ATR import ATR
from indicators.EMA import EMA
from indicators.STOCHRSI import STOCHRSI


class AtrSrsi3EmaStrategy(Strategy):
    """
    Simple AtrSrsi3EmaStrategy

    Parameters (4):
        risk_reward_ratio\n
        atr_factor\n
        investment_ratio\n
        interval_tolerance
    """

    MAX_OPEN_POSITIONS_NUMBER = 3

    def __init__(self, wallet_handler: WalletHandler, **strategy_params):
        self.risk_reward_ratio = strategy_params["risk_reward_ratio"]
        self.atr_factor = strategy_params["atr_factor"]
        self.investment_rate = strategy_params["investment_ratio"]
        self.interval_tolerance = strategy_params["interval_tolerance"]

        self.ema8 = EMA(period = 8)
        self.current_ema8 = np.nan
        self.ema14 = EMA(period = 14)
        self.current_ema14 = np.nan
        self.ema50 = EMA(period = 50)
        self.current_ema50 = np.nan

        self.stoch_rsi = STOCHRSI()
        self.current_k = np.nan
        self.last_k = np.nan
        self.current_d = np.nan
        self.last_d = np.nan
        self.atr = ATR()
        self.current_atr = np.nan
        super().__init__(wallet_handler, self.MAX_OPEN_POSITIONS_NUMBER)

    def compute_indicators_step(self, frame: DataFrame):
        close = frame.close_price
        high = frame.high_price
        low = frame.low_price
        self.current_ema8 = self.ema8.compute_next(close)
        self.current_ema14 = self.ema14.compute_next(close)
        self.current_ema50 = self.ema50.compute_next(close)
        self.last_k = self.current_k
        self.last_d = self.current_d
        self.current_k, self.current_d = self.stoch_rsi.compute_next(close)
        self.current_atr = self.atr.compute_next(high, low, close)

    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        if position_type == PositionType.LONG:
            return open_price - (self.atr_factor * self.current_atr)
        elif position_type == PositionType.SHORT:
            return open_price + (self.atr_factor * self.current_atr)

    def get_take_profit(self, open_price: float, position_type: PositionType) -> float:
        if position_type == PositionType.LONG:
            return open_price + (self.risk_reward_ratio * self.atr_factor * self.current_atr)
        elif position_type == PositionType.SHORT:
            return open_price - (self.risk_reward_ratio * self.atr_factor * self.current_atr)

    def get_margin_investment(self) -> float:
        return self.wallet_handler.get_balance() * self.investment_rate

    def get_long_conditions(self) -> List[StrategyCondition]:
        return [
            PerpetualStrategyCondition(self.long_perpetual_condition),
            EventStrategyCondition(self.long_event_condition, self.interval_tolerance)
        ]

    def get_short_conditions(self) -> List[StrategyCondition]:
        return [
            PerpetualStrategyCondition(self.short_perpetual_condition),
            EventStrategyCondition(self.short_event_condition, self.interval_tolerance)
        ]

    def long_perpetual_condition(self, frame: DataFrame) -> bool:
        close = frame.close_price
        if self.current_ema8 is np.nan or self.current_ema14 is np.nan or self.current_ema50 is np.nan: return False
        return self.current_ema50 < self.current_ema14 < self.current_ema8 < close

    def long_event_condition(self, frame: DataFrame) -> bool:
        if self.last_k is np.nan or self.current_k is np.nan or self.last_d is np.nan or self.current_d is np.nan: return False
        return self.last_k <= self.last_d and self.current_k > self.current_d

    def short_perpetual_condition(self, frame: DataFrame) -> bool:
        close = frame.close_price
        if self.current_ema8 is np.nan or self.current_ema14 is np.nan or self.current_ema50 is np.nan: return False
        return self.current_ema50 > self.current_ema14 > self.current_ema8 > close

    def short_event_condition(self, frame: DataFrame) -> bool:
        if self.last_k is np.nan or self.current_k is np.nan or self.last_d is np.nan or self.current_d is np.nan: return False
        return self.last_k >= self.last_d and self.current_k < self.current_d
