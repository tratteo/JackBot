import collections
import itertools
from collections import deque

import numpy as np


class RSI:

    def __init__(self, period: int = 14):
        self.period = period
        self.first_closes = deque(maxlen = period + 1)
        self.counter = 0
        self.prev = 0
        self.gain = 0
        self.loss = 0

    def __avg_gain_loss(self, closes):
        gain = []
        loss = []
        prev = closes[0]
        if len(closes) == 1:
            return [0, 0]

        for current in collections.deque(itertools.islice(closes, 1, len(closes))):
            if prev <= current:
                gain.append(current - prev)
                loss.append(0)
            elif prev > current:
                gain.append(0)
                loss.append(prev - current)
            prev = current

        return [np.mean(gain), np.mean(loss)]

    def compute_next(self, value):
        if self.counter <= self.period:
            self.counter += 1
            self.first_closes.append(value)
            self.gain, self.loss = self.__avg_gain_loss(self.first_closes)
        else:
            if self.prev <= value:
                self.gain = (self.gain * (self.period - 1) + (value - self.prev)) / self.period
                self.loss = (self.loss * (self.period - 1)) / self.period
            elif self.prev > value:
                self.loss = (self.loss * (self.period - 1) + (self.prev - value)) / self.period
                self.gain = (self.gain * (self.period - 1)) / self.period

        self.prev = value

        if self.counter < self.period + 1:
            return np.nan

        return 100 - (100 / (1 + (self.gain / self.loss)))
