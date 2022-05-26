import numpy as np


class MA:
    def __init__(self, period: int = 20):
        self.first_values = []
        self.period = period
        self.length = 0
        self.val = 0

    def compute_next(self, close: float) -> float:
        if self.length < self.period:
            self.first_values.append(close)
            self.length += 1
            return np.nan
        else:
            self.first_values.pop(0)
            self.first_values.append(close)
            self.val = sum(self.first_values)
            return self.val / float(self.period)

    def reset(self):
        self.length = 0
        self.val = 0
        self.first_values = []
