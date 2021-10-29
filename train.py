import importlib
import os
import sys

import config
from bot.command.command_handler import CommandHandler
from bot.training.genetic_trainer import GeneticTrainer, Gene
from bot import lib
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
    .keyed('-r', 'Epoch champion report') \
    .on_help(helper) \
    .on_fail(failure) \
    .build(sys.argv)

with open(command_manager.get_p(0)) as file:
    data = json.load(file)

dataset = command_manager.get_p(1)
strategy_name = data["strategy"]
strategy_class = getattr(importlib.import_module(config.DEFAULT_STRATEGIES_FOLDER + "." + strategy_name), strategy_name)
genome = [Gene(t["lower_bound"], t["upper_bound"], __try_get_json_attr("_value", t)) for t in data["parameters"]]
hyperparameters = data["hyperparameters"]

result_path = config.DEFAULT_RESULTS_PATH + strategy_name.lower() + ".res"
res_arg = command_manager.get_k("-o")
if res_arg is not None:
    result_path = res_arg

lib.create_folders_in_path(result_path, lambda: sys.exit(1))
report_path = command_manager.get_k("-r")
if report_path is not None:
    lib.create_folders_in_path(report_path)

if __name__ == '__main__':
    GeneticTrainer.train(strategy_class, genome, dataset, result_path,
                         crossover_operator = __try_get_json_attr("crossover_operator", hyperparameters),
                         crossover_rate = __try_get_json_attr("crossover_rate", hyperparameters),
                         mutation_type = __try_get_json_attr("mutation_type", hyperparameters),
                         mutation_rate = __try_get_json_attr("mutation_rate", hyperparameters),
                         population_number = __try_get_json_attr("population_number", hyperparameters),
                         processes_number = __try_get_json_attr("processes_number", hyperparameters),
                         max_iterations = __try_get_json_attr("max_iterations", hyperparameters),
                         report_path = report_path)
