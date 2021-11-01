import copy
import json
import math
import multiprocessing
import random
import time
from itertools import repeat

from numpy import genfromtxt

import config
from bot import dataset_evaluator
from bot.core import TestWallet, Strategy
from bot.dataset_evaluator import TestResult
from bot.lib import ProgressBar


class TrainingResult:
    def __init__(self, parameters: list[float], strategy: str):
        self.parameters = parameters
        self.strategy = strategy

    def to_json(self):
        return json.dumps(self.__dict__, default = lambda x: x.__dict__, indent = 4)


class Gene:
    def __init__(self, lower_bound: float = float("-inf"), upper_bound: float = float("inf"), value: float = None):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.value = value if value is not None else random.uniform(lower_bound, upper_bound)

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
        return "[" + str(self.lower_bound) + ", " + str(self.upper_bound) + "]: " + "{:.3f}".format(self.value)


class _Individual:

    def __init__(self, strategy_class: type, genome: list[Gene], deepcopy: bool = True):
        # Deepcopy the genome
        self.genome = copy.deepcopy(genome) if deepcopy else genome
        # Load the parameters into the strategy and instantiate it
        self.strategy_class = strategy_class
        self.fitness = 0
        self.test_result = None

    def build_strategy(self) -> Strategy:
        return self.strategy_class(TestWallet.factory(), *[g.value for g in self.genome])

    def __str__(self):
        s = "Strategy: " + str(self.strategy_class)
        s += "\nGenome: | "
        for g in self.genome: s += str(g) + " | "
        s += "\nFitness: " + str(self.fitness)
        s += "\n\nTest\n" + str(self.test_result)
        return s

    def calculate_fitness(self, test_result: TestResult) -> float:
        self.test_result = test_result
        positions_percentage = 0
        for p in test_result.closed_positions:
            val = p.result_percentage
            # if val < 0:
            #     val *= 1
            positions_percentage += val
        self.fitness = math.exp((math.pow(test_result.final_balance / test_result.initial_balance, 1.5) * positions_percentage * math.pow(test_result.win_ratio + 1, 1.5)) / (288 * test_result.days))
        if self.fitness < 0: self.fitness = 0
        return self.fitness


def train_strategy(strategy_class: type, ancestor_genome: list[Gene], data_path: str, result_path: str, **kwargs) -> any:
    # Optional parameters
    mutation_rate = kwargs.get("mutation_rate") if kwargs.get("mutation_rate") is not None else 0.1
    crossover_operator = kwargs.get("crossover_operator") if kwargs.get("crossover_operator") is not None else "uniform"
    crossover_rate = kwargs.get("crossover_rate") if kwargs.get("crossover_rate") is not None else 0.85
    population_number = kwargs.get("population_number") if kwargs.get("population_number") is not None else 6
    processes_number = kwargs.get("processes_number") if kwargs.get("processes_number") is not None else population_number if population_number <= config.MAX_PROCESSES_NUMBER else config.MAX_PROCESSES_NUMBER
    mutation_type = kwargs.get("mutation_type") if kwargs.get("mutation_type") is not None else "uniform"
    max_iterations = kwargs.get("max_iterations") if kwargs.get("max_iterations") is not None else float("inf")
    report_path = kwargs.get("report_path")

    population = []
    champion_fitness = 0
    champion = None
    epoch = 0
    print("Loading " + data_path + "...")
    data = genfromtxt(data_path, delimiter = config.DEFAULT_DELIMITER)
    progress_bar = ProgressBar.create(len(data)).width(30).no_percentage().build()
    workers_pool = multiprocessing.Pool(processes_number)

    print("Starting " + str(population_number) + " parallel simulations on " + str(data_path))

    # Instantiate random ancestors
    for i in range(population_number):
        population.append(_Individual(strategy_class, ancestor_genome))

    __mutation(population, mutation_type, mutation_rate)

    while epoch < max_iterations:
        epoch += 1
        avg_fitness = 0
        # Process data and run simulations
        progress_bar.reset()
        start = time.time()
        try:
            test_results_async = workers_pool.starmap_async(dataset_evaluator.evaluate, zip([i.build_strategy() for i in population], repeat(1000), repeat(data), repeat(progress_bar.step), repeat(1440), range(population_number)))
            test_results = test_results_async.get(timeout = 1000)
            if test_results is None:
                break

        except KeyboardInterrupt:
            workers_pool.terminate()
            workers_pool.join()
            break
        end = time.time()
        progress_bar.dispose()
        print("Epoch " + str(epoch) + " completed in " + str(end - start) + "s", flush = True)

        # Compute fitness and results
        for result, balance, index in test_results:
            avg_fitness += population.__getitem__(index).calculate_fitness(result)

        # Calculate champion
        epoch_champion = max(population, key = lambda x: x.fitness)

        if epoch_champion.fitness > champion_fitness:
            champion_fitness = epoch_champion.fitness
            champion = copy.deepcopy(epoch_champion)
            with open(result_path, "w") as res_out_file:
                res_out_file.write(TrainingResult([g.value for g in epoch_champion.genome], epoch_champion.strategy_class.__name__).to_json())
            # print("Evaluating champion...")
            # res, i = dataset_evaluator.evaluate(epoch_champion.strategy, 1000, data, None, False, 0)
            # print(str(res))
        if report_path is not None:
            with open(report_path, "w") as outfile:
                outfile.write("Epoch champion:\n")
                outfile.write(str(epoch_champion))
                if champion is not None:
                    outfile.write("\n" + "-" * 50)
                    outfile.write("\nChampion:\n")
                    outfile.write(str(champion))

        avg_fitness /= population_number
        print("Average fitness: " + str(avg_fitness), flush = True)
        print("Max fitness: " + str(epoch_champion.fitness), flush = True)
        print("Champion fitness: " + str(champion_fitness), flush = True)
        print("\n", flush = True)
        if epoch < max_iterations:
            # Crossover
            population = __crossover(population, crossover_rate, crossover_operator)
            # Mutation
            __mutation(population, mutation_type, mutation_rate)

    workers_pool.terminate()
    workers_pool.join()


def __selection_operator(population: list[_Individual]) -> [_Individual, _Individual]:
    sorted_pop = sorted(population, key = lambda x: x.fitness, reverse = True)
    return sorted_pop[0], sorted_pop[1]


# region Crossover

def __crossover(population: list[_Individual], crossover_rate: float, crossover_operator: str) -> list[_Individual]:
    new_population = []
    parent1, parent2 = __selection_operator(population)
    for i in range(len(population)):
        if random.random() < crossover_rate:
            new_genome = __crossover_operator(crossover_operator, parent1, parent2)
            new_population.append(_Individual(parent1.strategy_class, new_genome, False))
        else:
            if random.random() < 0.5:
                new_population.append(parent1)
            else:
                new_population.append(parent2)
    return new_population


def __crossover_operator(key: str, parent1: _Individual, parent2: _Individual) -> list[Gene]:
    new_genome = []

    if key == "uniform":
        # Uniform crossover operator
        for g1, g2 in zip(parent1.genome, parent2.genome):
            if random.random() < 0.5:
                new_genome.append(Gene(g1.lower_bound, g1.upper_bound, g1.value))
            else:
                new_genome.append(Gene(g1.lower_bound, g1.upper_bound, g2.value))
    elif key == "average":
        # Average crossover operator
        for g1, g2 in zip(parent1.genome, parent2.genome):
            new_genome.append(Gene(g1.lower_bound, g1.upper_bound, (g1.value + g2.value) / 2))

    elif key == "s-point":
        point = random.randint(0, len(parent1.genome) - 1)
        for i in parent1.genome[:point]:
            new_genome.append(i)
        for i in parent1.genome[point:]:
            new_genome.append(i)

    return new_genome


# endregion

# region Mutation

def __mutation(population: list[_Individual], mutation_type: str, mutation_rate: float):
    for p in population:
        __mutation_operator(mutation_type, p, mutation_rate)


def __mutation_operator(key: str, individual: _Individual, mutation_rate: float):
    if key == "uniform":
        for g in individual.genome:
            if random.random() < mutation_rate:
                g.value = random.uniform(g.lower_bound, g.upper_bound)
    elif key == "average":
        for g in individual.genome:
            if random.random() < mutation_rate:
                val = g.upper_bound - g.lower_bound
                if val > 1000: val = 1000 / 4
                g.value += random.gauss(0, val / 4)

# endregion
