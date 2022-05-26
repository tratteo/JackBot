import numpy as np

from core.bot.logic.condition import PerpetualStrategyCondition, EventStrategyCondition
from core.bot.logic.strategy import *
from indicators.EMA import EMA
from indicators.STOCHRSI import STOCHRSI


class MaSrsi3EmaStrategy(Strategy):

    def __init__(self, wallet_handler: WalletHandler, genome: dict, **strategy_params):
        self.risk_reward_ratio = genome["risk_reward_ratio"]
        self.stop_loss_ema = genome["stop_loss_ema_period"]
        self.investment_rate = genome["investment_ratio"]
        self.interval_tolerance = genome["interval_tolerance"]
        self.first_ema_period = genome["first_ema_period"]
        self.second_ema_period = genome["second_ema_period"]
        self.third_ema_period = genome["third_ema_period"]

        self.ema8 = EMA(period = round(self.first_ema_period))
        self.current_ema8 = np.nan
        self.ema14 = EMA(period = round(self.second_ema_period))
        self.current_ema14 = np.nan
        self.ema50 = EMA(period = round(self.third_ema_period))
        self.current_ema50 = np.nan

        self.stoch_rsi = STOCHRSI()
        self.current_k = np.nan
        self.last_k = np.nan
        self.current_d = np.nan
        self.last_d = np.nan
        self.sl_ema = EMA(period = round(self.stop_loss_ema))
        self.current_slema = np.nan
        super().__init__(wallet_handler, int(strategy_params.get("max_open_positions")))

    def compute_indicators_step(self, frame: DataFrame):
        close = frame.close_price
        self.current_ema8 = self.ema8.compute_next(close)
        self.current_ema14 = self.ema14.compute_next(close)
        self.current_ema50 = self.ema50.compute_next(close)
        self.last_k = self.current_k
        self.last_d = self.current_d
        self.current_k, self.current_d = self.stoch_rsi.compute_next(close)
        self.current_slema = self.sl_ema.compute_next(close)

    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        if position_type == PositionType.LONG:
            return self.current_slema
        elif position_type == PositionType.SHORT:
            return self.current_slema

    def get_take_profit(self, open_price: float, position_type: PositionType) -> float:
        if position_type == PositionType.LONG:
            return open_price + ((open_price - self.current_slema) * self.risk_reward_ratio)
        elif position_type == PositionType.SHORT:
            return open_price - ((self.current_slema - open_price) * self.risk_reward_ratio)

    def get_margin_investment(self) -> float:
        return self.wallet_handler.get_balance() * self.investment_rate

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
        if self.current_slema is np.nan or self.current_slema > close:
            return False
        if self.current_ema8 is np.nan or self.current_ema14 is np.nan or self.current_ema50 is np.nan: return False
        return self.current_ema50 < self.current_ema14 < self.current_ema8 < close

    def long_event_condition(self, frame: DataFrame) -> bool:
        if self.last_k is np.nan or self.current_k is np.nan or self.last_d is np.nan or self.current_d is np.nan: return False
        return self.last_k <= self.last_d and self.current_k > self.current_d

    def short_perpetual_condition(self, frame: DataFrame) -> bool:
        close = frame.close_price
        if self.current_slema is np.nan or self.current_slema < close:
            return False
        if self.current_ema8 is np.nan or self.current_ema14 is np.nan or self.current_ema50 is np.nan: return False
        return self.current_ema50 > self.current_ema14 > self.current_ema8 > close

    def short_event_condition(self, frame: DataFrame) -> bool:
        if self.last_k is np.nan or self.current_k is np.nan or self.last_d is np.nan or self.current_d is np.nan: return False
        return self.last_k >= self.last_d and self.current_k < self.current_d
