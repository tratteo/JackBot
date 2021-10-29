import importlib
import os
import sys

import config
from bot.command.command_handler import CommandHandler
from bot.training.genetic_trainer import GeneticTrainer, Gene
from strategies.StochRsiMacdStrategy import *


def __try_get_json_attr(key: str, json_obj):
    try:
        val = json_obj[key]
        return val
    except KeyError:
        return None


def helper(helper_str: str):
    print(helper_str)
    exit(0)


def failure(helper_str: str):
    print('Wrong syntax \n')
    print(helper_str)
    exit(1)


command_manager = CommandHandler.create() \
    .positional('Genetic parameters') \
    .positional('Dataset file') \
    .keyed('-o', 'Output file .res') \
    .keyed('-ec', 'Epoch champion report') \
    .on_help(helper) \
    .on_fail(failure) \
    .build(sys.argv)

with open(command_manager.get_p(0)) as file:
    data = json.load(file)

result_path = config.DEFAULT_RESULTS_PATH

dataset = command_manager.get_p(1)
strategy_name = data["strategy"]
strategy_class = getattr(importlib.import_module("strategies." + strategy_name), strategy_name)
genome = [Gene(t["lower_bound"], t["upper_bound"], __try_get_json_attr("_value", t)) for t in data["parameters"]]
hyperparameters = data["hyperparameters"]
if __name__ == '__main__':
    res = GeneticTrainer.train(strategy_class, genome, dataset,
                               crossover_operator = __try_get_json_attr("crossover_operator", hyperparameters),
                               crossover_rate = __try_get_json_attr("crossover_rate", hyperparameters),
                               mutation_type = __try_get_json_attr("mutation_type", hyperparameters),
                               mutation_rate = __try_get_json_attr("mutation_rate", hyperparameters),
                               population_number = __try_get_json_attr("population_number", hyperparameters),
                               processes_number = __try_get_json_attr("processes_number", hyperparameters),
                               max_iterations = __try_get_json_attr("max_iterations", hyperparameters),
                               epoch_champion_report_path = command_manager.get_k('-ec'))

    if res is not None:
        if not os.path.exists(result_path):
            try:
                os.makedirs(result_path)
            except FileExistsError:
                print("Something went wrong")
                sys.exit(1)

        path_key = command_manager.get_k('-o')
        path = result_path + strategy_name.lower() + "-train.res"
        if path_key is not None:
            path = path_key
        with open(path, "w") as outfile:
            outfile.write(res.to_json())
        print("\nOutput: " + path)
