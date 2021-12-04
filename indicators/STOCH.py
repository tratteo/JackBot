from collections import deque

import numpy as np
import talib as ta
from numpy import genfromtxt


class STOCH:

    def __init__(self, fastk_period: int = 14, slowk_period: int = 3, slowd_period: int = 3):
        self.fastk_period = fastk_period
        self.stoch = deque(maxlen = fastk_period)
        self.close = deque(maxlen = fastk_period)
        self.high = deque(maxlen = fastk_period)
        self.low = deque(maxlen = fastk_period)

        self.slowk_period = slowk_period
        self.slowd_period = slowd_period
        self.fastk = deque(maxlen = slowk_period)
        self.slowd = deque(maxlen = slowd_period)

    def compute_next(self, close: float, low: float, high: float) -> tuple[float, float]:
        self.high.append(high)
        self.low.append(low)
        self.close.append(close)
        min_val = np.min(self.low)
        max_val = np.max(self.high)
        # print("close ", self.close[-1], "min ", min_val, "max ", max_val)
        self.stoch.append((((self.close[-1] - min_val) / (max_val - min_val)) * 100))

        if len(self.stoch) == self.fastk_period:

            last_k = self.stoch[-1]
            self.fastk.append(last_k)

            if len(self.fastk) == self.slowk_period:
                new_k = np.sum(self.fastk) / self.slowk_period
            else:
                new_k = np.nan

            self.slowd.append(new_k)
            if len(self.slowd) == self.slowd_period:

                stoch_d = np.mean(self.slowd)
            else:
                stoch_d = np.nan

            return new_k, stoch_d

        else:
            return np.nan, np.nan


if __name__ == "__main__":

    stoch = STOCH()
    OPEN_T: int = 0
    HIGH: int = 2
    LOW: int = 3
    CLOSE: int = 4
    CLOSE_T: int = 6

    data = genfromtxt("../data/ETHUSDT_1-6_2021.csv", delimiter = ';')
    close = data[:, CLOSE][:100]
    high = data[:, HIGH][:100]
    low = data[:, LOW][:100]

    k_wind = []
    d_wind = []

    for i in range(len(close)):
        print(
            ta.STOCH(high, low, close, fastk_period = 14, slowk_period = 3, slowk_matype = 0, slowd_period = 3, slowd_matype = 0)[0][i],
            ta.STOCH(high, low, close, fastk_period = 14, slowk_period = 3, slowk_matype = 0, slowd_period = 3, slowd_matype = 0)[1][i])

        # print("his"  , stochastic(np.array(close[:i+1]), np.array(low[:i+1]), np.array(high[:i+1]), k_wind, d_wind) )

        print("my", stoch.compute_next(close[i], low[i], high[i]))
        print()
