import pandas
import numpy as np
import matplotlib.pyplot as plt


data = pandas.read_csv('analysisRes/cointegration.csv')
data = data.sort_values(by='df')

list =  data.iloc[0]['pair'].split('-')
file = 'data/' + list[0] + '_5m_1 Mar, 2022.csv'
x = pandas.read_csv(file, header=None)
x = (x[1] + x[4]) / 2
xm = x/np.mean(x)

file = 'data/' + list[1] + '_5m_1 Mar, 2022.csv'
y = pandas.read_csv(file, header=None)
y = (y[1] + y[4]) / 2
ym = y/np.mean(y)

fig, axs = plt.subplots(3)

axs[0].plot(ym)
axs[0].plot(xm)

axs[1].plot(xm/ym)

axs[2].plot(2*(xm - ym))



plt.show()

