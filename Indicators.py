import talib
from collections import deque
import numpy as np
import math

class Indicator:

    macdList = []
    smoothing = 2

    def MACD(self, closes):
        ema26 = talib.EMA(closes, timeperiod=26)
        ema12 = talib.EMA(closes, timeperiod=12)

        if len(self.macdList) > 35:
            signal = talib.EMA(np.array(self.macdList), timeperiod=9)
            #print(self.macdList)
        else:
            signal = [1]
        macd = ema12 - ema26
        if not math.isnan(macd[-1]) :
            self.macdList.append(macd[-1])
        return [macd, signal]