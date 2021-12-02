import collections
import itertools
import talib as ta
import numpy as np
from collections import deque
from numpy import genfromtxt
import config

class RSI:

    def __init__(self, period = 14):
        self.period = period
        self.first_closes = deque(maxlen=period+1)
        self.counter = 0
        self.prev = 0
        self.gain = 0
        self.loss = 0

    def avg_gain_loss(self, closes):
        gain = []
        loss = []
        prev = closes[0]
        if len(closes) == 1:
            return [0, 0]

        for c in collections.deque(itertools.islice(closes, 1, len(closes))):
            if prev <= c:
                gain.append(c - prev)
                loss.append(0)
            elif prev > c:
                gain.append(0)
                loss.append(prev - c)
            prev = c

        return [np.mean(gain), np.mean(loss)]


    def compute_next(self, value):
        if self.counter <= self.period :
            self.counter += 1
            self.first_closes.append(value)
            self.gain, self.loss = self.avg_gain_loss(self.first_closes)
        else:
            if self.prev <= value:
                self.gain = (self.gain*(self.period-1) + (value - self.prev))/self.period
                self.loss = (self.loss*(self.period-1))/self.period
            elif self.prev > value:
                self.loss = (self.loss*(self.period-1) + (self.prev - value))/self.period
                self.gain = (self.gain*(self.period-1))/self.period

        self.prev = value

        if self.counter < self.period +1:
            return np.nan

        return 100 - (100 / (1 + (self.gain / self.loss)))


if __name__ == "__main__":

    rsi = RSI()
    OPEN_T: int = 0
    HIGH: int = 2
    LOW: int = 3
    CLOSE: int = 4
    CLOSE_T: int = 6

    data = genfromtxt(r"..\bot\data\ETHUSDT_1-6_2021.csv", delimiter=config.DEFAULT_DELIMITER)
    close = data[:,CLOSE][:100]
    high = data[:,HIGH][:100]
    low = data[:,LOW][:100]

    print(len(high))

    for n, i in enumerate(close):
        print(n, " my ",  rsi.compute_next(i))
        print(n, " ta ", ta.RSI(close)[n])
        print()