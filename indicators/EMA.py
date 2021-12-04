import numpy as np
import talib as ta
from numpy import genfromtxt

import config


class EMA:
    def __init__(self, period: int = 20, smoothing: int = 2):
        self.smoothing = smoothing
        self.first_values = []
        self.previous_val = 0
        self.period = period

    def compute_next(self, close: float) -> float:
        if len(self.first_values) < self.period:
            self.first_values.append(close)
            self.previous_val = np.mean(self.first_values)
            return np.nan
        else:
            smooth = self.smoothing / (1 + self.period)
            self.previous_val = close * smooth + self.previous_val * (1 - smooth)
            return self.previous_val

    def reset(self):
        self.previous_val = 0
        self.first_values = []

# if __name__ == "__main__":
#     # TEST EMA
#
#     ema = EMA()
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
#
#     for n, i in enumerate(close):
#         print(n, " my ", ema.compute_next(i), " ta ", ta.EMA(close, 20)[n])
#     # print(ta.EMA(a, 20)[:200])
