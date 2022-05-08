import importlib
import json
import sys
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


command_manager = CommandHandler.create() \
    .positional("Genetic parameters") \
    .positional("Dataset file") \
    .on_help(helper) \
    .on_fail(failure) \
    .build(sys.argv)

if not exists(command_manager.get_p(0)):
    print("Unable to locate parameters file")
    exit(1)
with open(command_manager.get_p(0)) as file:
    data = json.load(file)

if not exists(command_manager.get_p(1)):
    print("Unable to locate dataset file")
    exit(1)

dataset_path = command_manager.get_p(1)


def main():
    # Init params
    rand = Random()
    rand.seed(int(time()))
    dataset = genfromtxt(dataset_path, delimiter = config.DEFAULT_DELIMITER)

    # Create EA
    my_ec = inspyred.ec.EvolutionaryComputation(rand)
    my_ec.terminator = [inspyred.ec.terminators.evaluation_termination]
    my_ec.variator = [mutator]
    my_ec.replacer = inspyred.ec.replacers.steady_state_replacement
    my_ec.observer = observer

    # Evolve
    final_pop = my_ec.evolve(generator = generator,
                             evaluator = inspyred.ec.evaluators.parallel_evaluation_mp,
                             bounder = bounder,
                             mp_evaluator = evaluator,
                             mp_num_cpus = config.MAX_PROCESSES_NUMBER,
                             maximize = True,
                             pop_size = 32,
                             max_evaluations = 1000,
                             mutation_rate = 0.15,
                             dataset = dataset,
                             strategy_class = getattr(importlib.import_module(config.DEFAULT_STRATEGIES_FOLDER + "." + data["strategy"]), data["strategy"]),
                             timeframe = lib.get_minutes_from_flag(data["timeframe"]),
                             parameters = data["parameters"])

    # Sort and print the best individual, who will be at index 0.
    final_pop.sort(reverse = True)
    print('Terminated due to {0}.'.format(my_ec.termination_cause))
    print(final_pop[0])


if __name__ == '__main__':
    main()
