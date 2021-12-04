from collections import deque

import numpy as np
import talib as ta
from numpy import genfromtxt

import config


class ATR:

    def __init__(self, period: int = 14):
        self.period = period
        self.prev_close = 0
        self.tr = deque(maxlen = period)
        self.atr = 0
        self.count = 0

    def compute_next(self, high: float, low: float, close: float) -> float:
        self.count += 1
        self.tr.append(max(high - low, abs(high - self.prev_close), abs(low - self.prev_close)))
        self.prev_close = close

        if self.count <= self.period + 1:
            self.atr = np.mean(self.tr)
            if self.count == self.period + 1:
                return (self.atr * (self.period - 1) + self.tr[-1]) / self.period
            else:
                return np.nan
        else:
            self.atr = (self.atr * (self.period - 1) + self.tr[-1]) / self.period
            return self.atr

# if __name__ == "__main__":
#
#     atr = ATR()
#
#     OPEN_T: int = 0
#     HIGH: int = 2
#     LOW: int = 3
#     CLOSE: int = 4
#     CLOSE_T: int = 6
#
#     data = genfromtxt(r"..\bot\data\ETHUSDT_1-6_2021.csv", delimiter = config.DEFAULT_DELIMITER)
#     close = data[:, CLOSE][:100]
#     high = data[:, HIGH][:100]
#     low = data[:, LOW][:100]
#     for (n, c), h, l in zip(enumerate(close), np.array(high), np.array(low)):
#         print(n, " my ", atr.compute_next(h, l, c))
#         print(n, " ta ", ta.ATR(np.array(high), np.array(low), np.array(close))[n])
#         print()
