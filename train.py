import importlib
import os
import sys

import config
from bot.training.genetic_trainer import GeneticTrainer, Gene
from strategies.StochRsiMacdStrategy import *


def __try_get_json_attr(key: str, json_obj):
    try:
        val = json_obj[key]
        return val
    except KeyError:
        return None


if len(sys.argv) == 1 or sys.argv[1] == "-h":
    print("train-genetic <options_file_path> <dataset> -results_folder-")
    sys.exit(0)

if len(sys.argv) < 3:
    print("Wrong parameters see usage with -h")
    sys.exit()

with open(sys.argv[1]) as file:
    data = json.load(file)

result_path = config.DEFAULT_RESULTS_PATH

dataset = sys.argv[2]
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
                               max_iterations = __try_get_json_attr("max_iterations", hyperparameters))

    if res is not None:
        if not os.path.exists(result_path):
            try:
                os.makedirs(result_path)
            except FileExistsError:
                print("Something went wrong")
                sys.exit(1)

        with open(result_path + strategy_name + "_train.res", "w") as outfile:
            outfile.write(res.to_json())
