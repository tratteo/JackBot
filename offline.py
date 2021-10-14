import math
import numpy as np
import talib
import pandas as pd


data = pd.read_csv('09_2020_data.csv')
# Open - time - Open - High - Low - Close - Volume Close time Quote asset volume	Number of trades	Taker buy base asset volume	Taker buy quote asset volume	Ignore
# more info: https://github.com/binance/binance-public-data/

# display(data)
#data = np.array(data)

closes = []
highs = []
lows = []

time = 0
while time < 287:  # numero di 5 minuti in 24 ore

    closes.append(data[time, 4])
    lows.append(data[time, 3])
    highs.append(data[time, 2])


exp1 = data.iloc[:,4].ewm(span=12, adjust=False).mean()
exp2 = data.iloc[:,4].ewm(span=26, adjust=False).mean()
macd = exp1-exp2
exp3 = macd.ewm(span=9, adjust=False).mean()

for num, i in enumerate(exp3):
    print(math.floor(num*5/60) + 2 , num*5%60 +5, 'signal', i)



plt.plot(range(0,287), macd, label='AMD MACD', color = '#EBD2BE')
plt.plot(range(0,287), exp3, label='Signal Line', color='#E5A4CB')
plt.legend(loc='upper left')
plt.show()


macd, signal, hist = talib.MACD(np.array(data.iloc[:,4]))


for num, i in enumerate(signal):
    print(math.floor(num*5/60) + 2 , num*5%60 +5, 'signal', i);
