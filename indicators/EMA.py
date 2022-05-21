import numpy as np


class EMA:
    def __init__(self, period: int = 20, smoothing: int = 2):
        self.smoothing = smoothing
        self.first_values = []
        self.previous_val = 0
        self.period = period
        self.length = 0

    def compute_next(self, close: float) -> float:
        if self.length < self.period:
            self.first_values.append(close)
            self.length += 1
            self.previous_val = np.mean(self.first_values)
            return np.nan
        else:
            smooth = self.smoothing / (1 + self.period)
            self.previous_val = close * smooth + self.previous_val * (1 - smooth)
            return self.previous_val

    def reset(self):
        self.length = 0
        self.previous_val = 0
        self.first_values = []
