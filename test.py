import numpy as np
import talib
from numpy import genfromtxt

HIGH: int = 2
LOW: int = 3
CLOSE: int = 4
data = genfromtxt('data/ETHUSDT_1-6_2021.csv', delimiter = ';')
highs = [d[HIGH] for d in data]
lows = [d[LOW] for d in data]
closes = [d[CLOSE] for d in data]
slowk, slowd = talib.STOCH(np.array(highs), np.array(lows), np.array(closes),
                           fastk_period = 14,
                           slowk_period = 1,
                           slowd_period = 3,
                           slowk_matype = 0, slowd_matype = 0)
for i, s in enumerate(slowk):
    if i < 100:
        print(str(i) + " " + str(s))
