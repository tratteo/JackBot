import numpy as np
import talib as technical

from core.bot.condition import EventStrategyCondition, PerpetualStrategyCondition, BoundedStrategyCondition
from core.bot.strategy import *


class Fibonacci50EmaRsi(Strategy):
    """
    70% winrate strategy based on 50 ema and RSI hidden divergences waiting for a bullish hammer pattern.

    Parameters (5):
            risk_reward_ratio\n
            atr_factor\n
            intervals_tolerance\n
            investment_ratio\n
            hidden_divergence_timeframe


    """
    MAX_OPEN_POSITIONS_NUMBER = 4

    def __init__(self, wallet_handler: WalletHandler, **strategy_params):
        self.risk_reward_ratio = strategy_params["risk_reward_ratio"]
        self.atr_factor = strategy_params["atr_factor"]
        self.intervals_tolerance = strategy_params["interval_tolerance"]
        self.investment_rate = strategy_params["investment_ratio"]
        self.hidden_divergence_timeframe = int(strategy_params["hidden_divergence_timeframe"])
        self.last_low_closes = 0
        self.last_high_closes = 0
        self.last_low_rsi = 0
        super().__init__(wallet_handler, self.MAX_OPEN_POSITIONS_NUMBER)

    def compute_indicators(self) -> list[tuple[str, any]]:
        return [
            ("atr", technical.ATR(np.array(self.highs), np.array(self.lows), np.array(self.closes))),
            ('rsi', technical.RSI(np.array(self.closes), 14)),
            ('50ema', technical.EMA(np.array(self.closes), timeperiod=50)),
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
        return [
            EventStrategyCondition(self.long_event_condition, self.intervals_tolerance),
            EventStrategyCondition(self.long_fib_condition, self.intervals_tolerance),
            EventStrategyCondition(self.long_50ema_condition, self.intervals_tolerance),
            EventStrategyCondition(self.long_rsi_condition, self.intervals_tolerance)
        ]

    def get_short_conditions(self) -> List[StrategyCondition]:
        return [
            EventStrategyCondition(self.short_event_condition, self.intervals_tolerance),
            EventStrategyCondition(self.short_fib_condition, self.intervals_tolerance),
            EventStrategyCondition(self.short_50ema_condition, self.intervals_tolerance),
            EventStrategyCondition(self.short_rsi_condition, self.intervals_tolerance)
        ]

    def short_50ema_condition(self, frame) -> bool:
        ema50 = self.get_indicator('50ema')
        return len(ema50) > 2 and self.closes[-2] < ema50[-2] and self.closes[-1] > ema50[-1]

    def short_fib_condition(self, frame) -> bool:
        return self.last_high_closes > 0 and self.__calculate_fibonacci_retracement(self.last_high_closes,
                                                                                    self.last_low_closes, 'down') < \
               self.closes[-1]

    def short_event_condition(self, frame) -> bool:
        if len(self.closes) > 0 and len(self.closes) > self.hidden_divergence_timeframe:
            self.last_low_closes = min(self.closes[-self.hidden_divergence_timeframe:-1])
            self.last_high_closes = max(self.closes[-self.hidden_divergence_timeframe:-1])
        else:
            self.last_low_closes = min(self.closes)
            self.last_high_closes = max(self.closes)
        return self.last_low_closes < self.closes[-1]

    def short_hammer_condition(self, frame) -> bool:
        hammer = self.__hammer_check(self.opens[-1],self.highs[-1],self.lows[-1],self.closes[-1])
        return hammer[-1] == 100 or hammer[-1] == -100

    def short_rsi_condition(self, frame) -> bool:
        rsi = self.get_indicator('rsi')
        if len(rsi) > 0 and len(rsi) > self.hidden_divergence_timeframe:
            self.last_low_rsi = min(rsi[-self.hidden_divergence_timeframe:-1])
        else:
            self.last_low_rsi = min(rsi)
        return self.last_low_rsi > rsi[-1]

    def long_50ema_condition(self, frame) -> bool:
        ema50 = self.get_indicator('50ema')
        return len(ema50) > 2 and self.closes[-2] > ema50[-2] and self.closes[-1] < ema50[-1]

    def long_fib_condition(self, frame) -> bool:
        return self.last_high_closes > 0 and self.__calculate_fibonacci_retracement(self.last_high_closes,
                                                                                    self.last_low_closes, 'up') > \
               self.closes[-1]

    def long_event_condition(self, frame) -> bool:
        if len(self.closes) > 0 and len(self.closes) > self.hidden_divergence_timeframe:
            self.last_low_closes = min(self.closes[-self.hidden_divergence_timeframe:-1])
            self.last_high_closes = max(self.closes[-self.hidden_divergence_timeframe:-1])
        else:
            self.last_low_closes = min(self.closes)
            self.last_high_closes = max(self.closes)

        return self.last_low_closes < self.closes[-1]

    def long_hammer_condition(self, frame) -> bool:
        hammer = self.__hammer_check(self.opens[-1], self.highs[-1], self.lows[-1], self.closes[-1])
        return hammer[-1] == 100 or hammer[-1] == -100

    def long_rsi_condition(self, frame) -> bool:
        rsi = self.get_indicator('rsi')
        if len(rsi) > 0 and len(rsi) > self.hidden_divergence_timeframe:
            self.last_low_rsi = min(rsi[-self.hidden_divergence_timeframe:-1])
        else:
            self.last_low_rsi = min(rsi)
        return self.last_low_rsi < rsi[-1]

    def __calculate_fibonacci_retracement(self, high, low, trend, level=0.5):
        """Fibonacci retracement levels: 0.236, 0.382, 0.500, 0.618, 0.764, 1.00, 1.382, 1.618"""
        if trend == 'up':
            return high - ((high - low) * level)
        if trend == 'down':
            return low + ((high - low) * level)

    def __hammer_check(self, open, high, low, close):
        if close > open:  # bullish
            head = close - open
            shadow = open - low
            if head * 2 <= shadow:
                return 1
            else:
                return 0
        else:  # bearish
            head = open - close
            shadow = high - close
            if head * 2 <= shadow:
                return -1
            else:
                return 0
