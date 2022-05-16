from collections import deque

import numpy as np

from indicators.RSI import RSI
from indicators.STOCH import STOCH


class STOCHRSI:

    def __init__(self, period: int = 14, fastk_period: int = 3, slowd_period: int = 3):
        self.period = period
        self.values = deque(maxlen = period)
        self.fastk_period = fastk_period
        self.slowd_period = slowd_period
        self.rsi = RSI(period = period)
        self.stoch = STOCH(fastk_period = period, slowd_period = fastk_period)

    def compute_next(self, close: float) -> tuple[float, float]:
        current = self.rsi.compute_next(close)
        self.values.append(current)

        min_val = np.min(self.values)
        max_val = np.max(self.values)
        diff = (max_val - min_val)
        diff = 1 if diff == 0 else diff
        fast_k = (((current - min_val) / diff) * 100)
        fast_d = self.stoch.compute_next(current, current, current)[0]

        if np.isnan(fast_d):
            return np.nan, np.nan

        return fast_k, fast_d
