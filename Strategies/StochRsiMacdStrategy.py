import numpy as np
import talib as technical

from Bot.Core import *


class StochRsiMacdStrategy(Strategy):
    STOCH_OVERBOUGHT = 82
    STOCH_OVERSOLD = 18
    STOCH_FAST_K = 14
    STOCH_SLOW_K = 1
    STOCH_SLOW_D = 3
    RSI_PERIOD = 14

    RISK_REWARD = 2
    ATR_FACTOR = 2
    MAX_OPEN_POSITIONS_NUMBER = 5
    INTERVALS_TOLERANCE_NUMBER = 4
    INVESTMENT_RATE = 0.25


    def __init__(self, wallet_handler: WalletHandler, handle_positions: bool = False):
        super().__init__(wallet_handler, self.MAX_OPEN_POSITIONS_NUMBER, handle_positions)
        self.long_conditions.append(EventStrategyCondition(self.macd_long_condition, self.INTERVALS_TOLERANCE_NUMBER))
        self.long_conditions.append(PerpetualStrategyCondition(self.long_perpetual_condition))
        self.long_conditions.append(DoubledStrategyCondition(self.long_necessary, self.long_cancel, self.INTERVALS_TOLERANCE_NUMBER))

        self.short_conditions.append(EventStrategyCondition(self.macd_short_condition, self.INTERVALS_TOLERANCE_NUMBER))
        self.short_conditions.append(PerpetualStrategyCondition(self.short_perpetual_condition))
        self.short_conditions.append(DoubledStrategyCondition(self.short_necessary, self.short_cancel, self.INTERVALS_TOLERANCE_NUMBER))


    def get_margin_investment(self):
        # TODO set a new margin investment strategy
        return self.wallet_handler.get_balance() * self.INVESTMENT_RATE


    def get_stop_loss(self, open_price: float, position_type: PositionType) -> float:
        atr = technical.ATR(np.array(self.highs), np.array(self.lows), np.array(self.closes))
        if position_type == PositionType.LONG:
            return open_price - (self.ATR_FACTOR * atr[-1])
        elif position_type == PositionType.SHORT:
            return open_price + (self.ATR_FACTOR * atr[-1])


    def get_take_profit(self, open_price: float, position_type: PositionType) -> float:
        atr = technical.ATR(np.array(self.highs), np.array(self.lows), np.array(self.closes))
        if position_type == PositionType.LONG:
            return open_price + (self.RISK_REWARD * self.ATR_FACTOR * atr[-1])
        elif position_type == PositionType.SHORT:
            return open_price - (self.RISK_REWARD * self.ATR_FACTOR * atr[-1])


    # region Conditions


    def long_cancel(self, frame) -> bool:
        stoch_k, stoch_d = technical.STOCH(np.array(self.highs), np.array(self.lows), np.array(self.closes),
                                           fastk_period=self.STOCH_FAST_K,
                                           slowk_period=self.STOCH_SLOW_K,
                                           slowd_period=self.STOCH_SLOW_D,
                                           slowk_matype=0, slowd_matype=0)
        last_stoch_k = stoch_k[-1]
        last_stoch_d = stoch_d[-1]
        return last_stoch_k > self.STOCH_OVERBOUGHT or last_stoch_d > self.STOCH_OVERBOUGHT


    def long_necessary(self, frame) -> bool:
        stoch_k, stoch_d = technical.STOCH(np.array(self.highs), np.array(self.lows), np.array(self.closes),
                                           fastk_period=self.STOCH_FAST_K,
                                           slowk_period=self.STOCH_SLOW_K,
                                           slowd_period=self.STOCH_SLOW_D,
                                           slowk_matype=0, slowd_matype=0)
        last_stoch_k = stoch_k[-1]
        last_stoch_d = stoch_d[-1]
        return last_stoch_k < self.STOCH_OVERSOLD and last_stoch_d < self.STOCH_OVERSOLD


    def short_cancel(self, frame) -> bool:
        stoch_k, stoch_d = technical.STOCH(np.array(self.highs), np.array(self.lows), np.array(self.closes),
                                           fastk_period=self.STOCH_FAST_K,
                                           slowk_period=self.STOCH_SLOW_K,
                                           slowd_period=self.STOCH_SLOW_D,
                                           slowk_matype=0, slowd_matype=0)
        last_stoch_k = stoch_k[-1]
        last_stoch_d = stoch_d[-1]
        return last_stoch_k < self.STOCH_OVERSOLD or last_stoch_d < self.STOCH_OVERSOLD


    def short_necessary(self, frame) -> bool:
        stoch_k, stoch_d = technical.STOCH(np.array(self.highs), np.array(self.lows), np.array(self.closes),
                                           fastk_period=self.STOCH_FAST_K,
                                           slowk_period=self.STOCH_SLOW_K,
                                           slowd_period=self.STOCH_SLOW_D,
                                           slowk_matype=0, slowd_matype=0)
        last_stoch_k = stoch_k[-1]
        last_stoch_d = stoch_d[-1]
        return last_stoch_k > self.STOCH_OVERBOUGHT and last_stoch_d > self.STOCH_OVERBOUGHT


    def macd_long_condition(self, frame):
        macd, signal, hist = technical.MACD(np.array(self.closes))
        return len(macd) > 2 and len(signal) > 2 and macd[-2] <= signal[-2] and macd[-1] > signal[-1]


    def macd_short_condition(self, frame):
        macd, signal, hist = technical.MACD(np.array(self.closes))
        return len(macd) > 2 and len(signal) > 2 and macd[-2] >= signal[-2] and macd[-1] < signal[-1]


    def long_perpetual_condition(self, frame) -> bool:
        macd, signal, hist = technical.MACD(np.array(self.closes))
        rsi = technical.RSI(np.array(self.closes), self.RSI_PERIOD)
        return rsi[-1] > 50 and macd[-1] >= signal[-1]


    def short_perpetual_condition(self, frame) -> bool:
        macd, signal, hist = technical.MACD(np.array(self.closes))
        rsi = technical.RSI(np.array(self.closes), self.RSI_PERIOD)
        return rsi[-1] < 50 and macd[-1] <= signal[-1]


    # endregion
