from collections import deque

import numpy as np
import talib as ta
from numpy import genfromtxt

import config
from indicators.RSI import RSI
from indicators.STOCH import STOCH


class STOCHRSI:

    def __init__(self, period = 14, fastk_period = 3, slowd_period = 3):
        self.period = period
        self.values = deque(maxlen = period)
        self.fastk_period = fastk_period
        self.slowd_period = slowd_period
        self.rsi = RSI(period = period)
        self.stoch = STOCH(fastk_period = period, slowd_period = fastk_period)

    def compute_next(self, value):
        current = self.rsi.compute_next(value)
        self.values.append(current)

        min_val = min(list(self.values))
        max_val = max(list(self.values))
        fastk = (((current - min_val) / (max_val - min_val)) * 100)
        fastd = self.stoch.compute_next(current, current, current)[0]

        if np.isnan(fastd):
            return np.nan, np.nan

        return fastk, fastd


if __name__ == "__main__":

    stochrsi = STOCHRSI()
    OPEN_T: int = 0
    HIGH: int = 2
    LOW: int = 3
    CLOSE: int = 4
    CLOSE_T: int = 6

    data = genfromtxt(r"..\bot\data\ETHUSDT_1-6_2021.csv", delimiter = config.DEFAULT_DELIMITER)
    close = data[:, CLOSE][:100]
    high = data[:, HIGH][:100]
    low = data[:, LOW][:100]

    for i in range(len(close)):
        print(
            ta.STOCHRSI(close, timeperiod = 14, fastk_period = 14, fastd_period = 3)[0][i],
            ta.STOCHRSI(close, timeperiod = 14, fastk_period = 14, fastd_period = 3)[1][i])

        # print("his"  , stochastic(np.array(close[:i+1]), np.array(low[:i+1]), np.array(high[:i+1]), k_wind, d_wind) )

        print("my", stochrsi.compute_next(close[i]))
        print()
