import numpy as np
import talib as technical

from bot.core import *


class AtrSrsi3EmaStrategy(Strategy):
    '''

    Simple AtrSrsi3EmaStrategy

    Parameters (3):
        risk_reward_ratio\n
        atr_factor\n
        investment_rate\n

    '''
    MAX_OPEN_POSITIONS_NUMBER = 5
    INTERVALS_TOLERANCE = 2

    def __init__(self, wallet_handler: WalletHandler, *strategy_params):
        self.risk_reward_ratio = strategy_params[0]
        self.atr_factor = strategy_params[1]
        self.investment_rate = strategy_params[2]
        super().__init__(wallet_handler, self.MAX_OPEN_POSITIONS_NUMBER)

    def compute_indicators(self) -> list[tuple[str, any]]:
        return [('8ema', technical.EMA(np.array(self.closes), timeperiod=8)),
                ('14ema', technical.EMA(np.array(self.closes), timeperiod=14)),
                ('50ema', technical.EMA(np.array(self.closes), timeperiod=50)),
                ('stoch_rsi', technical.STOCHRSI(np.array(self.closes), timeperiod=14, fastk_period=3, fastd_period=3)),
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
                EventStrategyCondition(self.long_event_condition, self.INTERVALS_TOLERANCE)
                ]

    def get_short_conditions(self) -> List[StrategyCondition]:
        return [PerpetualStrategyCondition(self.short_perpetual_condition),
                EventStrategyCondition(self.short_event_condition, self.INTERVALS_TOLERANCE)]

    def long_perpetual_condition(self, frame) -> bool:
        ema8, ema14, ema50 = self.get_indicator("8ema"), self.get_indicator('14ema'), self.get_indicator('50ema')

        return ema50[-1] < ema14[-1] < ema8[-1] < self.closes[-1]

    def long_event_condition(self, frame) -> bool:
        slow_k, slow_d = self.get_indicator('stoch_rsi')
        return len(slow_k) > 2 and len(slow_d) > 2 and slow_k[-2] <= slow_d[-2] and slow_k[-1] > slow_d[-1]

    def short_perpetual_condition(self, frame) -> bool:
        ema8, ema14, ema50 = self.get_indicator("8ema"), self.get_indicator('14ema'), self.get_indicator('50ema')

        return ema50[-1] > ema14[-1] > ema8[-1] > self.closes[-1]

    def short_event_condition(self, frame) -> bool:
        slow_k, slow_d = self.get_indicator('stoch_rsi')
        return len(slow_k) > 2 and len(slow_d) > 2 and slow_k[-2] >= slow_d[-2] and slow_k[-1] < slow_d[-1]
