import math

import numpy as np

from indicators.MA import MA


class BOLLINGERBANDS:
    def __init__(self, period: int = 20, stdev: int = 2):
        self.stdev = stdev
        self.ma = MA(period)
        self.period = period
        self.length = 0
        self.first_values = []

    def compute_next(self, close: float) -> (float, float):
        current_ma = self.ma.compute_next(close)
        if self.length < self.period:
            self.length += 1
            self.first_values.append(close)
            return np.nan, np.nan
        else:
            current_stdev = self.calculate_stdev(current_ma)
            return current_ma + (current_stdev * self.stdev), current_ma - (current_stdev * self.stdev)

    def reset(self):
        self.length = 0
        self.first_values = []
        self.ma.reset()

    def calculate_stdev(self, mean):
        cumulative = 0
        for v in self.first_values:
            cumulative += (v - mean) ** 2
        cumulative /= float(self.length)
        return math.sqrt(cumulative)
