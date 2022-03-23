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

    MAX_OPEN_POSITIONS_NUMBER = 2

    def __init__(self, wallet_handler: WalletHandler, **strategy_params):

        self.risk_reward_ratio = strategy_params["risk_reward_ratio"]
        self.atr_factor = strategy_params["atr_factor"]
        self.investment_rate = strategy_params["investment_ratio"]
        self.interval_tolerance = strategy_params["interval_tolerance"]
        self.leverage = strategy_params["leverage"]

        self.ema8 = EMA(period = 8)
        self.current_ema8 = {}
        self.ema14 = EMA(period = 14)
        self.current_ema14 = {}
        self.ema50 = EMA(period = 50)
        self.current_ema50 = {}

        self.stoch_rsi = STOCHRSI()
        self.current_k = {}
        self.last_k = {}
        self.current_d = {}
        self.last_d = {}
        self.atr = ATR()
        self.current_atr = {}
        super().__init__(wallet_handler, self.MAX_OPEN_POSITIONS_NUMBER)

    def compute_indicators_step(self, symbol,  frame):
        close = float(frame.close_time)
        high = float(frame.high_price)
        low = float(frame.low_price)
        self.current_ema8[symbol] = self.ema8.compute_next(close)
        self.current_ema14[symbol] = self.ema14.compute_next(close)
        self.current_ema50[symbol] = self.ema50.compute_next(close)
        self.last_k[symbol] = self.current_k
        self.last_d[symbol] = self.current_d
        self.current_k[symbol], self.current_d[symbol] = self.stoch_rsi.compute_next(close)
        self.current_atr[symbol] = self.atr.compute_next(high, low, close)

    def get_stop_loss(self, symbol, open_price: float, position_type: PositionType) -> float:
        if position_type == PositionType.LONG:
            return open_price - (self.atr_factor * self.current_atr[symbol])
        elif position_type == PositionType.SHORT:
            return open_price + (self.atr_factor * self.current_atr[symbol])

    def get_take_profit(self, symbol, open_price: float, position_type: PositionType) -> float:
        if position_type == PositionType.LONG:
            return open_price + (self.risk_reward_ratio * self.atr_factor * self.current_atr[symbol])
        elif position_type == PositionType.SHORT:
            return open_price - (self.risk_reward_ratio * self.atr_factor * self.current_atr[symbol])

    def get_leverage(self) -> float:
        return self.leverage

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

    def long_perpetual_condition(self, frame) -> bool:
        close = float(frame.close_price)
        symbol = frame.symbol
        if symbol is not self.current_ema8 or symbol is not self.current_ema14 or symbol is not self.current_ema50 : return False
        return self.current_ema50[symbol] < self.current_ema14[symbol] < self.current_ema8[symbol] < close

    def long_event_condition(self, frame) -> bool:
        symbol = frame.symbol
        if symbol is not self.last_k or symbol is not self.current_k or symbol is not self.last_d or symbol is not self.current_d: return False
        return self.last_k <= self.last_d and self.current_k > self.current_d

    def short_perpetual_condition(self, frame) -> bool:
        close = float(frame["c"])
        if self.current_ema8 is np.nan or self.current_ema14 is np.nan or self.current_ema50 is np.nan: return False
        return self.current_ema50 > self.current_ema14 > self.current_ema8 > close

    def short_event_condition(self, frame) -> bool:
        if self.last_k is np.nan or self.current_k is np.nan or self.last_d is np.nan or self.current_d is np.nan: return False
        return self.last_k >= self.last_d and self.current_k < self.current_d
