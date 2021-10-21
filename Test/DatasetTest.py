from numpy import genfromtxt

from Bot import DatasetEvaluator

from Strategies.StochRsiMacdStrategy import *

# RISK_REWARD = 3.528924149652328  # risk_reward_ratio
# ATR_FACTOR = 4.47931505562069  # atr_factor
# INTERVALS_TOLERANCE_NUMBER = 5.489476749691061  # interval_tolerance
# INVESTMENT_RATE = 0.5  # investment_rate
from Training import GeneticTrainer

params = [3.1891668590322118, 5, 6.910528767332698, 0.5]
res = DatasetEvaluator.evaluate(StochRsiMacdStrategy(None, *params),
                                1000,
                                genfromtxt('../Data/SOLUSDT_8-9_2021.csv', delimiter = ';'),
                                True)
print(res[0])
