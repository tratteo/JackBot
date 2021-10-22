import copy
import math
import multiprocessing
import random
import time
from itertools import repeat
from os import listdir
from os.path import isfile, join

from numpy import genfromtxt

from Bot import DatasetEvaluator
from Bot.DatasetEvaluator import TestResult
from Strategies.StochRsiMacdStrategy import StochRsiMacdStrategy


class _Gene:
    def __init__(self, lower_bound: float = float("-inf"), upper_bound: float = float("inf"), value: float = 0):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.value = value

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
        return "[" + str(self.lower_bound) + ", " + str(self.upper_bound) + "]: " + "{:.3f}".format(self._value)


class _Individual:

    def __init__(self, strategy_class: type, genome: list[_Gene], randomize: bool = False):
        # Deepcopy the genome
        self.genome = copy.deepcopy(genome)
        if randomize: self.randomize_genome()
        # Load the parameters into the strategy and instantiate it
        self.strategy = strategy_class(None, *[g.value for g in self.genome])
        self.fitness = 0
        self.test_result = None

    def __str__(self):
        s = "Strategy: " + str(type(self.strategy))
        s += "\nGenome: | "
        for g in self.genome: s += str(g) + " | "
        s += "\nFitness: " + str(self.fitness)
        s += "\n\nTest\n" + str(self.test_result)
        return s

    def randomize_genome(self):
        for g in self.genome:
            g.value = random.uniform(g.lower_bound, g.upper_bound)

    def calculate_fitness(self, test_result: TestResult) -> float:
        self.test_result = test_result
        fitness = math.exp(0.01 * test_result.estimated_apy) * pow(test_result.win_ratio, 1 / 2.5)
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
            print("=>", end = "")
            self.__batch_progress = 0

    @classmethod
    def train(cls, strategy_class: type, genome_constraints: list[tuple[float, float]], data_folder: str, **kwargs):
        cls().__train_strategy(strategy_class, genome_constraints, data_folder, **kwargs)

    def __train_strategy(self, strategy_class: type, genome_constraints: list[tuple[float, float]], data_folder: str, **kwargs):

        # Optional parameters
        mutation_rate = kwargs.get("mutation_rate") if kwargs.get("mutation_rate") is not None else 0.1
        crossover_operator = kwargs.get("crossover_operator") if kwargs.get("crossover_operator") is not None else "uniform"
        crossover_rate = kwargs.get("crossover_rate") if kwargs.get("crossover_rate") is not None else 1
        population_number = kwargs.get("population_number") if kwargs.get("population_number") is not None else 8
        processes_number = kwargs.get("processes_number") if kwargs.get("processes_number") is not None else population_number if population_number <= 16 else 16
        mutation_type = kwargs.get("mutation_type") if kwargs.get("mutation_type") is not None else "uniform"

        # Load data
        print("Loading data from " + data_folder)
        files = [f for f in listdir(data_folder) if isfile(join(data_folder, f))]
        sorted(files, key = lambda f: str(f[0]) + str(f[1]))
        data_arr = []
        for s in files:
            print("Loading " + s)
            data_arr.append(genfromtxt(data_folder + "/" + s, delimiter = ','))

        # Initialize
        population = []
        champion = None
        iterations = float("inf")
        epoch = 0
        data_index = 0
        data = data_arr[data_index]
        iterations_on_data = 1
        workers_pool = multiprocessing.Pool(processes = population_number)
        print("\nStarting " + str(population_number) + " parallel simulations on " + str(files[data_index]))

        # region Core

        # Instantiate random ancestors
        for i in range(population_number):
            population.append(_Individual(strategy_class, [_Gene(lower_bound, upper_bound) for lower_bound, upper_bound in genome_constraints], True))
        while epoch < iterations:
            self.__batch_progress = 0
            epoch += 1
            avg_fitness = 0
            # Check whether to switch dataset
            if epoch % iterations_on_data == 0:
                data_index += 1
                if data_index > len(data_arr) - 1: data_index = 0
                data = data_arr[data_index]
                print("Switching data to " + str(files[data_index]))

            # Process data and run simulations
            print("Processing epoch " + str(epoch) + " on " + str(files[data_index]))
            self.__total_progress_steps = len(data_arr[0]) * processes_number
            print("|>", end = "")
            start = time.time()
            test_results = workers_pool.starmap(DatasetEvaluator.evaluate, zip((i.strategy for i in population), repeat(1000), repeat(data), repeat(self.progress_report), repeat(False), range(0, population_number)))
            end = time.time()
            print("\nEpoch " + str(epoch) + " completed in " + str(end - start) + "s")

            # Compute fitness and results
            for result, index in test_results:
                avg_fitness += population[index].calculate_fitness(result)

            # Calculate champion
            epoch_champion = max(population, key = lambda x: x.fitness)
            if champion is None or epoch_champion.fitness > champion.fitness:
                champion = epoch_champion
                with open("champion.report", "w") as outfile:
                    outfile.write(str(champion))
            avg_fitness /= population_number
            print("Average fitness: " + str(avg_fitness))
            print("Epoch max fitness: " + str(epoch_champion.fitness))
            print("Champion fitness: " + str(champion.fitness))
            print("\n")
            # Crossover
            population = self.__crossover(population, crossover_rate, crossover_operator)
            # Mutation
            self.__mutation(population, mutation_type, mutation_rate)

        # endregion

    # region Crossover

    def __crossover(self, population: list[_Individual], crossover_rate: float, crossover_operator: str) -> list[_Individual]:
        new_population = []
        population.sort(key = lambda x: x.fitness, reverse = True)
        parent1, parent2 = population[0], population[1]
        for i in range(len(population)):
            if random.random() < crossover_rate:
                new_genome = self.__apply_crossover_operator(crossover_operator, parent1, parent2)
                new_population.append(_Individual(type(parent1.strategy), new_genome))
            else:
                if random.random() < 0.5:
                    new_population.append(parent1)
                else:
                    new_population.append(parent2)
        return new_population

    def __apply_crossover_operator(self, key: str, parent1: _Individual, parent2: _Individual) -> list[_Gene]:
        new_genome = []
        match key:
            case "uniform":
                # Uniform crossover operator
                for g1, g2 in zip(parent1.genome, parent2.genome):
                    if random.random() < 0.5:
                        new_genome.append(_Gene(g1.lower_bound, g1.upper_bound, g1.value))
                    else:
                        new_genome.append(_Gene(g1.lower_bound, g1.upper_bound, g2.value))
            case "average":
                # Average crossover operator
                for g1, g2 in zip(parent1.genome, parent2.genome):
                    new_genome.append(_Gene(g1.lower_bound, g1.upper_bound, (g1.value + g2.value) / 2))
        return new_genome

    # endregion

    # region Mutation

    def __mutation(self, population: list[_Individual], mutation_type: str, mutation_rate: float):
        count = 0
        for p in population:
            self.__apply_mutation_operator(mutation_type, p, mutation_rate)

    def __apply_mutation_operator(self, key: str, individual: _Individual, mutation_rate: float):
        match key:
            case "uniform":
                for g in individual.genome:
                    if random.random() < mutation_rate:
                        g.value = random.uniform(g.lower_bound, g.upper_bound)
            case "gaussian":
                for g in individual.genome:
                    if random.random() < mutation_rate:
                        val = g.upper_bound - g.lower_bound
                        if val > 1000: val = 1000 / 5
                        g.value += random.gauss(0, val / 5)

    # endregion


if __name__ == '__main__':
    GeneticTrainer.train(StochRsiMacdStrategy,
                         [(1, 3.5), (1, 3), (2, 10), (0.01, 0.2), (70, 90), (10, 30)],
                         "../GeneticTrainData",
                         crossover_operator = "average",
                         crossover_rate = 0.75,
                         mutation_type = "uniform",
                         mutation_rate = 0.2,
                         population_number = 8,
                         processes_number = 8)
