import numpy as np
import talib as technical

from bot.core import *


class StochRsiMacdStrategy(Strategy):
    """
    Simple STOCH, MACD, RSI strategy.

    Parameters (6):
        risk_reward_ratio\n
        atr_factor\n
        intervals_tolerance\n
        investment_rate\n
        stoch_overbought\n
        stoch_oversold
    """

    STOCH_FAST_K = 14
    STOCH_SLOW_K = 1
    STOCH_SLOW_D = 3
    RSI_PERIOD = 14
    MAX_OPEN_POSITIONS_NUMBER = 4

    def __init__(self, wallet_handler: WalletHandler, *strategy_params):
        self.risk_reward_ratio = strategy_params[0]
        self.atr_factor = strategy_params[1]
        self.intervals_tolerance = strategy_params[2]
        self.investment_rate = strategy_params[3]
        self.stoch_overbought = strategy_params[4]
        self.stoch_oversold = strategy_params[5]
        super().__init__(wallet_handler, self.MAX_OPEN_POSITIONS_NUMBER)

    def compute_indicators(self) -> list[tuple[str, any]]:
        return [
            ("stoch", technical.STOCH(np.array(self.highs), np.array(self.lows), np.array(self.closes),
                                      fastk_period = self.STOCH_FAST_K,
                                      slowk_period = self.STOCH_SLOW_K,
                                      slowd_period = self.STOCH_SLOW_D,
                                      slowk_matype = 0, slowd_matype = 0)),
            ("atr", technical.ATR(np.array(self.highs), np.array(self.lows), np.array(self.closes))),
            ("rsi", technical.RSI(np.array(self.closes), self.RSI_PERIOD)),
            ("macd", technical.MACD(np.array(self.closes)))]

    def get_margin_investment(self):
        # TODO set a new margin investment strategy
        return self.wallet_handler.get_balance() * self.investment_rate

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

    def get_long_conditions(self) -> List[StrategyCondition]:
        return [
            BoundedStrategyCondition(self.long_necessary, self.long_cancel, self.intervals_tolerance),
            PerpetualStrategyCondition(self.long_perpetual_condition),
            EventStrategyCondition(self.macd_long_condition, self.intervals_tolerance)
        ]
        pass

    def get_short_conditions(self) -> List[StrategyCondition]:
        return [
            EventStrategyCondition(self.macd_short_condition, self.intervals_tolerance),
            PerpetualStrategyCondition(self.short_perpetual_condition),
            BoundedStrategyCondition(self.short_necessary, self.short_cancel, self.intervals_tolerance)
        ]
        pass

    # region Conditions

    def long_cancel(self, frame) -> bool:
        stoch_k, stoch_d = self.get_indicator("stoch")
        last_stoch_k = stoch_k[-1]
        last_stoch_d = stoch_d[-1]
        return last_stoch_k > self.stoch_overbought or last_stoch_d > self.stoch_overbought

    def long_necessary(self, frame) -> bool:
        stoch_k, stoch_d = self.get_indicator("stoch")
        last_stoch_k = stoch_k[-1]
        last_stoch_d = stoch_d[-1]
        return last_stoch_k < self.stoch_oversold and last_stoch_d < self.stoch_oversold

    def short_cancel(self, frame) -> bool:
        stoch_k, stoch_d = self.get_indicator("stoch")
        last_stoch_k = stoch_k[-1]
        last_stoch_d = stoch_d[-1]
        return last_stoch_k < self.stoch_oversold or last_stoch_d < self.stoch_oversold

    def short_necessary(self, frame) -> bool:
        stoch_k, stoch_d = self.get_indicator("stoch")
        last_stoch_k = stoch_k[-1]
        last_stoch_d = stoch_d[-1]
        return last_stoch_k > self.stoch_overbought and last_stoch_d > self.stoch_overbought

    def macd_long_condition(self, frame):
        macd, signal, hist = self.get_indicator("macd")
        return len(macd) > 2 and len(signal) > 2 and macd[-2] <= signal[-2] and macd[-1] > signal[-1]

    def macd_short_condition(self, frame):
        macd, signal, hist = self.get_indicator("macd")
        return len(macd) > 2 and len(signal) > 2 and macd[-2] >= signal[-2] and macd[-1] < signal[-1]

    def long_perpetual_condition(self, frame) -> bool:
        macd, signal, hist = self.get_indicator("macd")
        rsi = self.get_indicator("rsi")
        return rsi[-1] > 50  # and macd[-1] >= signal[-1]

    def short_perpetual_condition(self, frame) -> bool:
        macd, signal, hist = self.get_indicator("macd")
        rsi = self.get_indicator("rsi")
        return rsi[-1] < 50  # and macd[-1] <= signal[-1]

    # endregion
