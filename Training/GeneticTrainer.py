import copy
import multiprocessing
import random
import threading
import time
from typing import List, Generic, TypeVar

from numpy import genfromtxt

from Bot import DatasetEvaluator


class Gene:
    def __init__(self, lower_bound: float = float("-inf"), upper_bound: float = float("inf"), value: float = 0):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self._value = value

    @classmethod
    def random(cls, lower_bound: float = float("-inf"), upper_bound: float = float("inf")):
        return cls(lower_bound, upper_bound, random.uniform(lower_bound, upper_bound))

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value: float):
        if self.lower_bound < value:
            self._value = value
        else:
            self._value = self.lower_bound

        if self.upper_bound > value:
            self._value = value
        else:
            self._value = self.upper_bound

    def __str__(self):
        return "[" + str(self.lower_bound) + ", " + str(self.upper_bound) + "]: " + str(self.value)


class Individual:

    def __init__(self, genome: List[Gene], randomize: bool = False):
        self.genome = copy.deepcopy(genome)
        if randomize: self.randomize_genome()

    def randomize_genome(self):
        for g in self.genome:
            g.value = random.uniform(g.lower_bound, g.upper_bound)


class GeneticTrainer:

    def __init__(self, initial_genome: List[Gene], strategy_factory):
        self.initial_genome = initial_genome
        self.strategy_factory = strategy_factory

    def run(self):
        pop_n = 8
        population = []
        for i in range(pop_n):
            population.append(Individual(self.initial_genome, True))

        workers = []
        # TODO pass parameters to evaluate only on certain part of data
        # implement a convolution window on data
        data = genfromtxt('../Data/ETHUSDT_1-6_2021.csv', delimiter = ';')
        for i in range(pop_n):
            thread = multiprocessing.Process(target = DatasetEvaluator.evaluate, args = (self.strategy_factory, 1000, data, True, i))
            workers.append(thread)
            thread.start()

        for p in workers:
            p.join()

        # evaluate individuals fitness
        # perform crossover and mutation
        # instantiate a new class
        pass
