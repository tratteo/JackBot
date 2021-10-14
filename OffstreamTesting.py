import math
import numpy as np
import talib
import pandas as pd
import json
from numpy import genfromtxt

# data = pd.read_csv('09_2020_data.csv')
data = genfromtxt('09_2020_data.csv',delimiter=',')

CANDLE_TIME=5
time=0


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


while time<6:
    mess["k"]["c"]=str(data[time, 4])
    mess["k"]["h"] = str(data[time, 2])
    mess["k"]["l"] = str(data[time, 3])
    if time % CANDLE_TIME == 0:
        mess["k"]["x"] = True
    else:
        mess["k"]["x"] = False
    out = json.dumps(mess)
    print(out)
    time += 1



