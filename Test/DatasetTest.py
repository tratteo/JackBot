from numpy import genfromtxt

from Bot import DatasetEvaluator

from Strategies.StochRsiMacdStrategy import *
from Training.GeneticTrainer import GeneticTrainer, Gene

# res = DatasetEvaluator.evaluate(StochRsiMacdStrategy, 1000, genfromtxt('../Data/ETHUSDT_1-6_2021.csv', delimiter = ';'), True)
# print(res)

if __name__ == '__main__':
    gen = GeneticTrainer([Gene(-1, 1), Gene(-5, 5), Gene(0, 10)], StochRsiMacdStrategy)
    gen.run()
