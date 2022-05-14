import json
import sys
from os.path import exists

from core.command_handler import CommandHandler
from core.evolutionary import evolutionary_computation


def helper(helper_str: str):
    print(helper_str, flush = True)
    exit(0)


def failure(helper_str: str):
    print("Wrong syntax \n", flush = True)
    print(helper_str, flush = True)
    exit(1)


if __name__ == '__main__':

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
        parameters_json = json.load(file)

    if not exists(command_manager.get_p(1)):
        print("Unable to locate dataset folder")
        exit(1)

    dataset_path = command_manager.get_p(1)

    champ = evolutionary_computation.evolve_parallel(parameters_json, dataset_path,
                                                     pop_size = 24,
                                                     generations = 200,
                                                     mutation_rate = 0.25,
                                                     crossover_rate = 0.8,
                                                     processes = 8,
                                                     dataset_epochs = 5)
