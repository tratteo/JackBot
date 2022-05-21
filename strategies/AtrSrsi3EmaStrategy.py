import numpy as np

from core.bot.logic.condition import PerpetualStrategyCondition, EventStrategyCondition
from core.bot.logic.strategy import *
from indicators.ATR import ATR
from indicators.EMA import EMA
from indicators.STOCHRSI import STOCHRSI


class AtrSrsi3EmaStrategy(Strategy):
    """
    Simple AtrSrsi3EmaStrategy

    Parameters (7):
        risk_reward_ratio\n
        atr_factor\n
        investment_ratio\n
        interval_tolerance\n
        first_ema_period\n
        second_ema_period\n
        third_ema_period
    """

    def __init__(self, wallet_handler: WalletHandler, genome: dict, **strategy_params):
        self.investment_ratio = genome["investment_ratio"]
        self.interval_tolerance = genome["interval_tolerance"]
        self.first_ema_period = genome["first_ema_period"]
        self.second_ema_period = genome["second_ema_period"]
        self.third_ema_period = genome["third_ema_period"]

        self.first_ema = EMA(period = round(self.first_ema_period))
        self.current_first_ema = np.nan
        self.second_ema = EMA(period = round(self.second_ema_period))
        self.current_second_ema = np.nan
        self.third_ema = EMA(period = round(self.third_ema_period))
        self.current_third_ema = np.nan

        self.stoch_rsi = STOCHRSI()
        self.current_k = np.nan
        self.last_k = np.nan
        self.current_d = np.nan
        self.last_d = np.nan
        self.atr = ATR()
        self.current_atr = np.nan
        super().__init__(wallet_handler, int(strategy_params.get("max_open_positions")))

    def compute_indicators_step(self, frame: DataFrame):
        close = frame.close_price
        high = frame.high_price
        low = frame.low_price
        self.current_first_ema = self.first_ema.compute_next(close)
        self.current_second_ema = self.second_ema.compute_next(close)
        self.current_third_ema = self.third_ema.compute_next(close)
        self.last_k = self.current_k
        self.last_d = self.current_d
        self.current_k, self.current_d = self.stoch_rsi.compute_next(close)
        self.current_atr = self.atr.compute_next(high, low, close)

    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        if position_type == PositionType.LONG:
            return open_price - (3 * self.current_atr)
        elif position_type == PositionType.SHORT:
            return open_price + (3 * self.current_atr)

    def get_take_profit(self, open_price: float, position_type: PositionType) -> float:
        if position_type == PositionType.LONG:
            return open_price + (2 * self.current_atr)
        elif position_type == PositionType.SHORT:
            return open_price - (2 * self.current_atr)

    def get_margin_investment(self) -> float:
        return self.wallet_handler.get_balance() * self.investment_ratio

    def build_long_conditions(self) -> List[StrategyCondition]:
        return [
            PerpetualStrategyCondition(self.long_perpetual_condition),
            EventStrategyCondition(self.long_event_condition, self.interval_tolerance)
        ]

    def build_short_conditions(self) -> List[StrategyCondition]:
        return [
            PerpetualStrategyCondition(self.short_perpetual_condition),
            EventStrategyCondition(self.short_event_condition, self.interval_tolerance)
        ]

    def long_perpetual_condition(self, frame: DataFrame) -> bool:
        close = frame.close_price
        if self.current_first_ema is np.nan or self.current_second_ema is np.nan or self.current_third_ema is np.nan:
            return False
        return self.current_third_ema < self.current_second_ema < self.current_first_ema < close

    def long_event_condition(self, frame: DataFrame) -> bool:
        if self.last_k is np.nan or self.current_k is np.nan or self.last_d is np.nan or self.current_d is np.nan:
            return False
        return self.last_k <= self.last_d and self.current_k > self.current_d

    def short_perpetual_condition(self, frame: DataFrame) -> bool:
        close = frame.close_price
        if self.current_first_ema is np.nan or self.current_second_ema is np.nan or self.current_third_ema is np.nan:
            return False
        return self.current_third_ema > self.current_second_ema > self.current_first_ema > close

    def short_event_condition(self, frame: DataFrame) -> bool:
        if self.last_k is np.nan or self.current_k is np.nan or self.last_d is np.nan or self.current_d is np.nan:
            return False
        return self.last_k >= self.last_d and self.current_k < self.current_d
