from collections import deque

import numpy as np
import talib as ta
from numpy import genfromtxt

import config


class STOCH:

    def __init__(self, fastk_period = 14, slowk_period = 3, slowd_period = 3):
        self.fastk_period = fastk_period
        self.stoch = deque(maxlen = fastk_period)
        self.close = deque(maxlen = fastk_period)
        self.high = deque(maxlen = fastk_period)
        self.low = deque(maxlen = fastk_period)

        self.slowk_period = slowk_period
        self.slowd_period = slowd_period
        self.fastk = deque(maxlen = slowk_period)
        self.slowd = deque(maxlen = slowd_period)

    def compute_next(self, close, low, high):
        self.high.append(high)
        self.low.append(low)
        self.close.append(close)

        min_val = min(list(self.low))
        max_val = max(list(self.high))
        # print("close ", self.close[-1], "min ", min_val, "max ", max_val)
        self.stoch.append((((np.array(self.close) - min_val) / (max_val - min_val)) * 100)[-1])

        if len(self.stoch) == self.fastk_period:

            last_k = self.stoch[-1]
            self.fastk.append(last_k)

            if len(self.fastk) == self.slowk_period:
                new_k = np.array(self.fastk).sum() / self.slowk_period
            else:
                new_k = np.nan

            self.slowd.append(new_k)
            if len(self.slowd) == self.slowd_period:

                D = np.array(self.slowd).mean()
            else:
                D = np.nan

            return new_k, D

        else:
            return np.nan, np.nan


if __name__ == "__main__":

    stoch = STOCH()
    OPEN_T: int = 0
    HIGH: int = 2
    LOW: int = 3
    CLOSE: int = 4
    CLOSE_T: int = 6

    data = genfromtxt(r"..\bot\data\ETHUSDT_1-6_2021.csv", delimiter = config.DEFAULT_DELIMITER)
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
