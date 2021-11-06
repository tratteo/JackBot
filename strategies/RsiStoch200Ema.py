import numpy as np
import talib as technical

from core.bot.condition import EventStrategyCondition, PerpetualStrategyCondition, BoundedStrategyCondition
from core.bot.strategy import *


class RsiStoch200Ema(Strategy):
    """
        STOCH, 200EMA, RSI strategy.

        Parameters (6):
            risk_reward_ratio\n
            atr_factor\n
            intervals_tolerance\n
            investment_ratio\n
            stoch_overbought\n
            stoch_oversold
        """
    MAX_OPEN_POSITIONS_NUMBER = 4

    def __init__(self, wallet_handler: WalletHandler, **strategy_params):
        self.risk_reward_ratio = strategy_params["risk_reward_ratio"]
        self.atr_factor = strategy_params["atr_factor"]
        self.intervals_tolerance = strategy_params["interval_tolerance"]
        self.investment_rate = strategy_params["investment_ratio"]
        self.hidden_divergence_timeframe = int(strategy_params["hidden_divergence_timeframe"])
        self.last_low_closes = 0
        self.last_low_rsi = 0
        super().__init__(wallet_handler, self.MAX_OPEN_POSITIONS_NUMBER)

    def compute_indicators(self) -> list[tuple[str, any]]:
        return [
            ("stoch", technical.STOCH(np.array(self.highs), np.array(self.lows), np.array(self.closes),
                                      fastk_period=14,
                                      slowk_period=1,
                                      slowd_period=3,
                                      slowk_matype=0, slowd_matype=0)),
            ("atr", technical.ATR(np.array(self.highs), np.array(self.lows), np.array(self.closes))),
            ("rsi", technical.RSI(np.array(self.closes), 14)),
            ('200ema', technical.EMA(np.array(self.closes), timeperiod=200))]

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
        return [
            EventStrategyCondition(self.long_stoch_condition, self.intervals_tolerance),
            EventStrategyCondition(self.long_event_condition, self.intervals_tolerance),
            PerpetualStrategyCondition(self.long_perpetual_condition)
        ]

    def get_short_conditions(self) -> List[StrategyCondition]:
        return [
            EventStrategyCondition(self.short_stoch_condition, self.intervals_tolerance),
            EventStrategyCondition(self.short_event_condition, self.intervals_tolerance),
            PerpetualStrategyCondition(self.short_perpetual_condition)
        ]

    def long_perpetual_condition(self, frame) -> bool:
        ema200 = self.get_indicator("200ema")
        return self.closes[-1] > ema200[-1]

    def short_perpetual_condition(self, frame) -> bool:
        ema200 = self.get_indicator("200ema")
        return self.closes[-1] < ema200[-1]

    def long_event_condition(self, frame) -> bool:

        if len(self.closes) > 0 and len(self.closes) > self.hidden_divergence_timeframe:
            self.last_low_closes = min(self.closes[-self.hidden_divergence_timeframe:-1])
        else:
            self.last_low_closes = min(self.closes)

        return self.last_low_closes < self.closes[-1]

    def short_event_condition(self, frame) -> bool:

        if len(self.closes) > 0 and len(self.closes) > self.hidden_divergence_timeframe:
            self.last_low_closes = min(self.closes[-self.hidden_divergence_timeframe:-1])
        else:
            self.last_low_closes = min(self.closes)

        return self.last_low_closes > self.closes[-1]

    def long_rsi_condition(self, frame) -> bool:
        rsi = self.get_indicator('rsi')
        if len(rsi) > 0 and len(rsi) > self.hidden_divergence_timeframe:
            self.last_low_rsi = min(rsi[-self.hidden_divergence_timeframe:-1])
        else:
            self.last_low_rsi = min(rsi)
        return self.last_low_rsi > self.rsi[-1]

    def long_rsi_condition(self, frame) -> bool:
        rsi = self.get_indicator('rsi')
        if len(rsi) > 0 and len(rsi) > self.hidden_divergence_timeframe:
            self.last_low_rsi = min(rsi[-self.hidden_divergence_timeframe:-1])
        else:
            self.last_low_rsi = min(rsi)
        return self.last_low_rsi < self.rsi[-1]

    def long_stoch_condition(self, frame) -> bool:
        slow_k, slow_d = self.get_indicator('stoch')
        return len(slow_k) > 2 and len(slow_d) > 2 and slow_k[-2] <= slow_d[-2] and slow_k[-1] > slow_d[-1]

    def short_stoch_condition(self, frame) -> bool:
        slow_k, slow_d = self.get_indicator("stoch")
        return len(slow_k) > 2 and len(slow_d) > 2 and slow_k[-2] >= slow_d[-2] and slow_k[-1] < slow_d[-1]
