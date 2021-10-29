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
        self.strategy = strategy_class(TestWallet.factory(), *[g.value for g in self.genome])
        self.fitness = 0
        self.test_result = None

    def __str__(self):
        s = "Strategy: " + str(type(self.strategy))
        s += "\nGenome: | "
        for g in self.genome: s += str(g) + " | "
        s += "\nFitness: " + str(self.fitness)
        s += "\n\nTest\n" + str(self.test_result)
        return s

    def to_json(self):
        return json.dumps(self.__dict__, default = self.__serializer_guard, indent = 4)

    @staticmethod
    def __serializer_guard(obj):
        if isinstance(obj, Strategy): return str(type(obj).__name__)
        return obj.__dict__

    def calculate_fitness(self, test_result: TestResult) -> float:
        self.test_result = test_result
        fitness = math.exp(0.75 * ((test_result.final_balance / test_result.initial_balance) - 1))  # * pow(test_result.win_ratio, 2)
        if fitness < 0: fitness = 0
        self.fitness = fitness
        return self.fitness


class GeneticTrainer:

    def __init__(self):
        self.__batch_progress = 0
        self.__total_progress_steps = 0

    def progress_report(self, p: float):
        self.__batch_progress += p
        if self.__batch_progress >= self.__total_progress_steps * 0.02:
            print("\b", end = "", flush = True)
            print("=>", end = "", flush = True)
            self.__batch_progress = 0

    @classmethod
    def train(cls, strategy_class: type, ancestor_genome: list[Gene], data_path: str, result_path: str, **kwargs) -> any:
        """Train the selected strategy hyperparameters.

        NOTE: len(genome_constraints) must be equal to the len(strategy_params)"""
        return cls().__train_strategy(strategy_class, ancestor_genome, data_path, result_path, **kwargs)

    def __train_strategy(self, strategy_class: type, ancestor_genome: list[Gene], data_path: str, result_path: str, **kwargs) -> any:
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
        epoch = 0
        print("Loading " + data_path + "...")
        data = genfromtxt(data_path, delimiter = config.DEFAULT_DELIMITER)

        workers_pool = multiprocessing.Pool(population_number)

        print("Starting " + str(population_number) + " parallel simulations on " + str(data_path))

        # Instantiate random ancestors
        for i in range(population_number):
            population.append(_Individual(strategy_class, ancestor_genome))

        while epoch < max_iterations:
            self.__batch_progress = 0
            epoch += 1
            avg_fitness = 0
            # Process data and run simulations
            print("\nProcessing epoch " + str(epoch))
            self.__total_progress_steps = len(data) * processes_number
            print("|>", end = "", flush = True)

            start = time.time()
            try:
                test_results_async = workers_pool.starmap_async(dataset_evaluator.evaluate, zip([i.strategy for i in population], repeat(1000), repeat(data), repeat(self.progress_report), repeat(False), range(population_number)))
                test_results = test_results_async.get(timeout = 1000)
                if test_results is None:
                    break

            except KeyboardInterrupt:
                workers_pool.terminate()
                workers_pool.join()
                break
            end = time.time()
            print("\n\nEpoch " + str(epoch) + " completed in " + str(end - start) + "s")

            # Compute fitness and results
            for result, index in test_results:
                avg_fitness += population.__getitem__(index).calculate_fitness(result)

            # Calculate champion
            epoch_champion = max(population, key = lambda x: x.fitness)
            if epoch_champion.fitness > champion_fitness:
                champion_fitness = epoch_champion.fitness
                if report_path is not None:
                    with open(report_path, "w") as outfile:
                        outfile.write(epoch_champion.to_json())
                with open(result_path, "w") as res_out_file:
                    res_out_file.write(TrainingResult([g.value for g in epoch_champion.genome], type(epoch_champion.strategy).__name__).to_json())
                # print("Evaluating champion...")
                # res, i = dataset_evaluator.evaluate(epoch_champion.strategy, 1000, data, None, False, 0)
                # print(str(res))

            avg_fitness /= population_number
            print("Average fitness: " + str(avg_fitness))
            print("Max fitness: " + str(epoch_champion.fitness))
            print("Champion fitness: " + str(champion_fitness))
            if epoch < max_iterations:
                # Crossover
                population = self.__crossover(population, crossover_rate, crossover_operator)
                # Mutation
                self.__mutation(population, mutation_type, mutation_rate)

        workers_pool.terminate()
        workers_pool.join()

    @staticmethod
    def __selection_operator(population: list[_Individual]) -> [_Individual, _Individual]:
        sorted_pop = sorted(population, key = lambda x: x.fitness, reverse = True)
        return sorted_pop[0], sorted_pop[1]

    # region Crossover

    def __crossover(self, population: list[_Individual], crossover_rate: float, crossover_operator: str) -> list[_Individual]:
        new_population = []
        parent1, parent2 = self.__selection_operator(population)
        for i in range(len(population)):
            if random.random() < crossover_rate:
                new_genome = self.__crossover_operator(crossover_operator, parent1, parent2)
                new_population.append(_Individual(type(parent1.strategy), new_genome, False))
            else:
                if random.random() < 0.5:
                    new_population.append(parent1)
                else:
                    new_population.append(parent2)
        return new_population

    @staticmethod
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

    def __mutation(self, population: list[_Individual], mutation_type: str, mutation_rate: float):
        for p in population:
            self.__mutation_operator(mutation_type, p, mutation_rate)

    @staticmethod
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
