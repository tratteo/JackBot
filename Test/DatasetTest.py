from numpy import genfromtxt

from Bot import DatasetEvaluator

from Strategies.StochRsiMacdStrategy import *

params = [3, 2, 6, 0.2, 85, 15]
print("Evaluating...")
res = DatasetEvaluator.evaluate(StochRsiMacdStrategy(None, *params), 1000, genfromtxt('../Data/ETHUSDT_1-6_2021.csv', delimiter = ';'), None)
print(res[0])
