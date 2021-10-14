import json

import numpy as np
import talib as technical
# data = pd.read_csv('09_2020_data.csv')
from numpy import genfromtxt

from Strategies.StochRsiMacdStrategy import StochRsiMacdStrategy


data = genfromtxt('09_2020_data.csv', delimiter=',')

CANDLE_TIME = 5
time = 0

mess = {
    "e": "kline",
    "E": 123456789,
    "s": "BNBBTC",
    "k": {
        "t": 123400000,
        "T": 123460000,
        "s": "BNBBTC",
        "i": "1m",
        "f": 100,
        "L": 200,
        "o": "0.0010",
        "c": "close",
        "h": "high",
        "l": "low",
        "v": "1000",
        "n": 100,
        "x": 'isClosed',
        "q": "1.0000",
        "V": "500",
        "Q": "0.500",
        "B": "123456"
        }
    }

high = data[time, 2]  # dati di default
low = data[time, 3]

start_time = 0
highs = []
lows = []
closes = []

strat = StochRsiMacdStrategy()

while time < 10080:  # len(data) -1:
    mess["k"]["c"] = str(data[time, 4])
    mess["k"]["h"] = str(data[time, 2])
    mess["k"]["l"] = str(data[time, 3])
    mess["k"]["t"] = str(data[time, 0])
    mess["k"]["T"] = str(data[time, 6])
    if high < data[time, 2]:
        high = data[time, 2]

    if low > data[time, 3]:
        low = data[time, 3]

    if time != 0 and (time % CANDLE_TIME) == CANDLE_TIME - 1:
        mess["k"]["x"] = True
        mess["k"]["h"] = str(high)
        mess["k"]["l"] = str(low)
        mess["k"]["t"] = start_time
        mess["k"]["T"] = data[time, 6]
        highs.append(float(mess["k"]["h"]))
        lows.append(float(mess["k"]["l"]))
        closes.append(float(mess["k"]["c"]))
        high = data[time + 1, 2]  # setto i dati default alla prima candelotta aperta
        low = data[time + 1, 3]
        start_time = data[time + 1, 0]

        stoch_k, stoch_d = technical.STOCH(np.array(highs), np.array(lows), np.array(closes),
                                           fastk_period=14,
                                           slowk_period=1,
                                           slowd_period=3,
                                           slowk_matype=0, slowd_matype=0)
        macd, signal, hist = technical.MACD(np.array(closes))
        rsi = technical.RSI(np.array(closes), 14)

        strat.update_state(mess)
        # print("\n 5 min candle: " + str(mess))
        # print("RSI: " + str(rsi[-1]) + ", STOCH: " + str(stoch_k[-1]) + ", " + str(stoch_d[-1]) + ", MACD: " + str(macd[-1]) + ", " + str(signal[-1]))

    else:
        mess["k"]["x"] = False
    out = json.dumps(mess)
    # print(out)
    time += 1
