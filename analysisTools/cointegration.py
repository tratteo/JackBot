import os
import re
from pprint import pprint
import numpy as np
import json
import csv
import pandas
import statsmodels.api as sm
import statsmodels.tsa.stattools as ts
import matplotlib.pyplot as plt


def cointegration_test(y, x):
    model = sm.OLS(y, x)
    ols_result = model.fit()

    return ts.adfuller(ols_result.resid)


results = []
symb2 = os.listdir('data')
for s1 in os.listdir('data')[:2]:
    symb2.remove(s1)

    if len(symb2) > 0:
        for s2 in symb2:
            print(s1, s2)

            y = pandas.read_csv(os.path.join('data', s1), header=None)
            x = pandas.read_csv(os.path.join('data', s2), header=None)

            y = (y[1] + y[4]) / 2
            x = (x[1] + x[4]) / 2

            if len(y) > len(x):
                y = y[:len(x)]
            else:
                x = x[:len(y)]

            save = []
            save.append(re.findall("^[^_]+", s1)[0] + "-" + re.findall("^[^_]+", s2)[0])
            res = cointegration_test(y, x)
            for i in range(3):
                save.append(res[i])

            results.append(save)

with open('../analysisRes/cointegration.csv', "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerows(results)
