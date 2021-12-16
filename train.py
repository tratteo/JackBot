import importlib
import json
import sys

import config
from core import lib
from core.command_handler import CommandHandler
from core.training import genetic_trainer
from core.training.genetic_trainer import Gene


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
    .keyed("-o", "Output file .res") \
    .keyed("-r", "Epoch report") \
    .keyed("-ib", "Initial balance") \
    .keyed("-v", "Validation set file") \
    .keyed("-vr", "Validation report file") \
    .on_help(helper) \
    .on_fail(failure) \
    .build(sys.argv)

with open(command_manager.get_p(0)) as file:
    data = json.load(file)

# Get args
dataset = command_manager.get_p(1)
strategy_name = data["strategy"]
hyperparameters = data["hyperparameters"]
timeframe = lib.get_minutes_from_flag(data["timeframe"])

initial_balance = 10000
arg = command_manager.get_k("-ib")
if arg is not None: initial_balance = int(arg)

result_path = command_manager.get_k("-o")
if result_path is None: result_path = config.DEFAULT_RESULTS_PATH + strategy_name.lower() + ".res"
lib.create_folders_in_path(result_path, lambda: sys.exit(1))

report_path = command_manager.get_k("-r")
if report_path is not None:
    lib.create_folders_in_path(report_path)

# Instantiate the strategy
strategy_class = getattr(importlib.import_module(config.DEFAULT_STRATEGIES_FOLDER + "." + strategy_name), strategy_name)
genome = [Gene(t["name"], t["lower_bound"], t["upper_bound"], lib.try_get_json_attr("_value", t)) for t in data["parameters"]]
# Train parallel
if __name__ == "__main__":
    try:
        genetic_trainer.train_strategy(strategy_class, genome, dataset, result_path,
                                       crossover_operator = lib.try_get_json_attr("crossover_operator", hyperparameters),
                                       crossover_rate = lib.try_get_json_attr("crossover_rate", hyperparameters),
                                       mutation_type = lib.try_get_json_attr("mutation_type", hyperparameters),
                                       mutation_rate = lib.try_get_json_attr("mutation_rate", hyperparameters),
                                       population_number = lib.try_get_json_attr("population_number", hyperparameters),
                                       processes_number = lib.try_get_json_attr("processes_number", hyperparameters),
                                       validation_interval = lib.try_get_json_attr("validation_interval", hyperparameters),
                                       validation_set_path = command_manager.get_k("-v"),
                                       validation_report_path = command_manager.get_k("-vr"),
                                       initial_balance = initial_balance,
                                       timeframe = timeframe,
                                       report_path = report_path)
    except(KeyboardInterrupt, SystemExit):
        exit(0)
