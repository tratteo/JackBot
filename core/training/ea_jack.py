import importlib
import json
import sys
from multiprocessing import Manager
from os import listdir
from os.path import exists
from random import Random
from time import time

import inspyred
from numpy import genfromtxt

import config
from core.command_handler import CommandHandler
from core.training.operators import *


def helper(helper_str: str):
    print(helper_str, flush = True)
    exit(0)


def failure(helper_str: str):
    print("Wrong syntax \n", flush = True)
    print(helper_str, flush = True)
    exit(1)


def load_data(path: str, datasets):
    datasets.append()


def main(sync_manager: Manager):
    # Init params
    command_manager = CommandHandler.create() \
        .positional("Genetic parameters") \
        .positional("Dataset folder") \
        .on_help(helper) \
        .on_fail(failure) \
        .build(sys.argv)

    if not exists(command_manager.get_p(0)):
        print("Unable to locate parameters file")
        exit(1)
    with open(command_manager.get_p(0)) as file:
        data = json.load(file)

    if not exists(command_manager.get_p(1)):
        print("Unable to locate dataset folder")
        exit(1)

    dataset_path = command_manager.get_p(1)
    rand = Random()
    rand.seed(int(time()))
    onlyfiles = [f for f in listdir(dataset_path) if f.endswith(".CSV") or f.endswith(".csv")]
    print("Found {0} files in {1}".format(len(onlyfiles), dataset_path))
    datasets = []

    for f in onlyfiles:
        # datasets.append(genfromtxt(dataset_path + "//" + f, delimiter = config.DEFAULT_DELIMITER))
        print("Loading {0}...".format(f), flush = True)
        datasets.append(genfromtxt(dataset_path + "//" + f, delimiter = config.DEFAULT_DELIMITER))

    # Create EA
    ec = inspyred.ec.EvolutionaryComputation(rand)
    ec.terminator = [inspyred.ec.terminators.generation_termination, inspyred.ec.terminators.average_fitness_termination]
    ec.variator = [gaussian_adj_mutator, inspyred.ec.variators.uniform_crossover]
    ec.selector = inspyred.ec.selectors.tournament_selection
    ec.replacer = inspyred.ec.replacers.random_replacement
    ec.observer = observer
    # Evolve
    print("Starting evolution", flush = True)

    final_pop = ec.evolve(
        # Operators
        evaluator = inspyred.ec.evaluators.parallel_evaluation_mp,
        generator = generator,
        bounder = bounder,
        mp_evaluator = evaluator,
        mp_num_cpus = 4,
        # TODO add a method to append iterations test results
        # Variation
        mutation_rate = 0.2,
        crossover_rate = 0.75,
        # Selection
        num_selected = 64,
        tournament_size = 8,
        # Parameters
        maximize = True,
        pop_size = 64,
        max_generations = 150,
        num_elites = 8,
        # Custom params
        datasets = datasets,
        lock = sync_manager.Lock(),
        job_index = sync_manager.Value("job_index", 0),
        cache_path = ".cache/",
        dataset_epochs = 10,
        strategy_class = getattr(importlib.import_module(config.DEFAULT_STRATEGIES_FOLDER + "." + data["strategy"]), data["strategy"]),
        timeframe = lib.get_minutes_from_flag(data["timeframe"]),
        parameters = data["parameters"])

    # Sort and print the best individual, who will be at index 0.
    final_pop.sort(reverse = True)
    print('Terminated due to {0}.'.format(ec.termination_cause))
    print(final_pop[0])


if __name__ == '__main__':
    with Manager() as manager:
        main(manager)
