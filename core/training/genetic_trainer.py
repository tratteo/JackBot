import copy
import json
import math
import multiprocessing
import random
import time
from itertools import repeat
from os import listdir
from os.path import join, isfile

from numpy import genfromtxt

import config
from core import lib
from core.bot import dataset_evaluator
from core.bot.strategy import Strategy
from core.bot.dataset_evaluator import TestResult
from core.lib import ProgressBar
from core.bot.wallet_handler import TestWallet


class Gene:
    def __init__(self, name: str, lower_bound: float = float("-inf"), upper_bound: float = float("inf"), value: float = None):
        self.name = name
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.value = value if value is not None else random.uniform(lower_bound, upper_bound)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val: float):
        if self.lower_bound < val < self.upper_bound:
            self._value = val
        else:
            self._value = self.lower_bound if val < self.lower_bound else self.upper_bound

    def __str__(self):
        return "{:<25s}[{:.2f}, {:.2f}]: {:.2f}".format(self.name, self.lower_bound, self.upper_bound, self.value)


class TrainingResult:
    def __init__(self, parameters: list[Gene], strategy: str, timeframe: str):
        self.strategy = strategy
        self.timeframe = timeframe
        self.parameters = parameters

    def to_json(self):
        return json.dumps(self.__dict__, default = lambda x: x.__dict__, indent = 4)


class _Individual:

    def __init__(self, strategy_class: type, genome: list[Gene], deepcopy: bool = True):
        # Deepcopy the genome
        self.genome = copy.deepcopy(genome) if deepcopy else genome
        # Load the parameters into the strategy and instantiate it
        self.strategy_class = strategy_class
        self.fitness = 0
        self.test_result = None

    def build_strategy(self, initial_balance: int) -> Strategy:
        return self.strategy_class(TestWallet.factory(initial_balance), **dict([(p.name, p.value) for p in self.genome]))

    def __str__(self):
        s = "Strategy: " + str(self.strategy_class)
        s += "\n\nGenome:\n"
        for index, gene in enumerate(self.genome):
            s += str(gene) + "\n"
        s += "\nFitness: " + str(self.fitness)
        s += "\n\nTest:\n" + str(self.test_result)
        return s

    def calculate_fitness(self, test_result: TestResult) -> float:
        self.test_result = test_result
        positions_percentage = 0
        for p in test_result.closed_positions:
            val = p.result_percentage
            # losses are 15% more serious
            # if val < 0: val *= 1.15
            positions_percentage += val
        balance_ratio = test_result.final_balance / test_result.initial_balance
        self.fitness = math.exp(balance_ratio * positions_percentage * math.pow(test_result.win_ratio + 1, 1.75) / (test_result.minutes / test_result.time_frame_minutes))
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
    max_iterations = kwargs.get("max_iterations") if kwargs.get("max_iterations") is not None else 10
    timeframe = kwargs.get("timeframe") if kwargs.get("timeframe") is not None else 5
    initial_balance = kwargs.get("initial_balance") if kwargs.get("initial_balance") is not None else 10000
    report_path = kwargs.get("report_path")
    validation_set_path = kwargs.get("validation_set_path") if kwargs.get("validation_set_path") is not None else None

    population = []
    champion = None
    epoch = 0
    validation_data = None
    validation_interval = max_iterations
    validation_progress_bar = None

    if validation_set_path is not None:
        print("Loading validation set " + validation_set_path + "...")
        validation_data = genfromtxt(validation_set_path, delimiter = config.DEFAULT_DELIMITER)
        if validation_data is None: return
        validation_progress_bar = ProgressBar.create(len(validation_data)).width(30).no_percentage().build()
    print("Loading " + data_path + "...")
    data = genfromtxt(data_path, delimiter = config.DEFAULT_DELIMITER)
    if data is None: return
    workers_pool = multiprocessing.Pool(processes_number)
    progress_bar = ProgressBar.create(len(data)).width(30).no_percentage().build()

    print("\nStarting " + str(population_number) + " parallel simulations on " + str(data_path) + " | " + lib.get_flag_from_minutes(timeframe) + "\n")

    # Instantiate random ancestors
    for i in range(population_number):
        population.append(_Individual(strategy_class, ancestor_genome))

    __mutation(population, mutation_type, mutation_rate)

    while epoch < float("inf"):
        avg_fitness = 0
        # Process data and run simulations
        start = time.time()
        print("Epoch " + str(epoch + 1))
        progress_bar.reset()
        test_results_async = workers_pool.starmap_async(
            dataset_evaluator.evaluate,
            zip([i.build_strategy(initial_balance) for i in population],
                repeat(initial_balance),
                repeat(data),
                repeat(progress_bar.step),
                repeat(1440),
                repeat(timeframe),
                range(population_number)))

        test_results = test_results_async.get(timeout = 1000)
        if test_results is None: break

        end = time.time()
        progress_bar.dispose()
        print("Epoch " + str(epoch + 1) + " completed in " + "{:.3f}".format(end - start) + "s", flush = True)

        # Compute fitness and results
        for result, balance, index in test_results:
            avg_fitness += population[index].calculate_fitness(result)

        # Calculate champion
        epoch_champion = max(population, key = lambda x: x.fitness)

        if champion is None or epoch_champion.fitness > champion.fitness:
            champion = copy.deepcopy(epoch_champion)
            with open(result_path, "w") as res_out_file:
                res_out_file.write(TrainingResult([g for g in epoch_champion.genome], epoch_champion.strategy_class.__name__, lib.get_flag_from_minutes(timeframe)).to_json())
            # print("Evaluating champion...")
            # res, i = dataset_evaluator.evaluate(epoch_champion.strategy, 1000, data, None, False, 0)
            # print(str(res))
        if report_path is not None:
            with open(report_path, "w") as outfile:
                outfile.write("Epoch champion:\n")
                outfile.write(str(epoch_champion))
                if champion is not None:
                    outfile.write("\n\n" + "-" * 100 + "\n")
                    outfile.write("\nChampion:\n")
                    outfile.write(str(champion))

        avg_fitness /= population_number
        print("Average fitness: " + str(avg_fitness), flush = True)
        print("Max fitness: " + str(epoch_champion.fitness), flush = True)
        print("Champion fitness: " + str(champion.fitness), flush = True)
        print("\n", flush = True)
        # Crossover
        population = __crossover(population, crossover_rate, crossover_operator)
        # Mutation
        __mutation(population, mutation_type, mutation_rate)
        epoch += 1
        validation_interval -= 1
        if champion is not None and validation_set_path is not None and validation_interval == 0:
            print("Running champion on validation set")
            validation_progress_bar.reset()
            result, balance, index = dataset_evaluator.evaluate(champion.build_strategy(initial_balance), initial_balance, validation_data, validation_progress_bar.step, 1440, timeframe, 0)
            if result is None: break
            validation_progress_bar.dispose()
            validation_interval = max_iterations
            print(str(result) + "\n")

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
                new_genome.append(Gene(g1.name, g1.lower_bound, g1.upper_bound, g1.value))
            else:
                new_genome.append(Gene(g1.name, g1.lower_bound, g1.upper_bound, g2.value))
    elif key == "average":
        # Average crossover operator
        for g1, g2 in zip(parent1.genome, parent2.genome):
            new_genome.append(Gene(g1.name, g1.lower_bound, g1.upper_bound, (g1.value + g2.value) / 2))

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
    elif key == "gaussian":
        for g in individual.genome:
            if random.random() < mutation_rate:
                val = g.upper_bound - g.lower_bound
                g.value += random.gauss(0, val / 3)

# endregion
