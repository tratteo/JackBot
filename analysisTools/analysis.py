
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from CexLib.Kucoin.KucoinData import KucoinData

KData = KucoinData(os.environ.get('FK_KEY'), os.environ.get('FK_SECRET'), os.environ.get('FK_PASS'))

print(os.getcwd())
data = pd.read_csv(r'analysisTools/cointegration.csv')

data = data.sort_values(by='df')
window = 192
end_training = 550
start = datetime.datetime(2022, 3, 14)
end = datetime.datetime(2022, 3, 28)

list = []
for i in range(10):
    list =  data.iloc[i]['pair'].split('-')
    print(list)

    file = np.array(pd.read_csv(os.path.join('data1', list[0] + '_302022-03-14 00:00:002022-03-28 00:00:00.csv')))
    meanPrice = (file[:,1] + file[:,4]) / 2
    dates = file[:,0]
    dates = [datetime.datetime.utcfromtimestamp(int(i)/1000).strftime('%Y-%m-%d %H:%M') for i in dates]
    xm = np.array(meanPrice) / (np.array(pd.DataFrame(meanPrice).rolling(window=window).mean()).T)[0]

    file = np.array(pd.read_csv(os.path.join('data1', list[1] + '_302022-03-14 00:00:002022-03-28 00:00:00.csv')))
    meanPrice = (file[:, 1] + file[:, 4]) / 2
    ym = np.array(meanPrice) / (np.array(pd.DataFrame(meanPrice).rolling(window=window).mean()).T)[0]

    if len(xm) < len(ym):
        ym = ym[:len(xm)]
    else:
        xm = xm[:len(ym)]

    fig, axs = plt.subplots(2)
    fig.suptitle(list[0] + " " + list[1])

    axs[0].plot(dates, ym,  label= list[0])
    axs[0].plot(xm, label=list[1])

    axs[0].legend()
    axs[0].axvline(x=end_training, color='r')
    axs[1].axvline(x=end_training, color='r')
    axs[1].plot(dates,xm - ym)

    every_nth = 100
    for n, label in enumerate(axs[0].xaxis.get_ticklabels()):
        if n % every_nth != 0:
            label.set_visible(False)

    for n, label in enumerate(axs[1].xaxis.get_ticklabels()):
        if n % every_nth != 0:
            label.set_visible(False)

    plt.show()


