import importlib
import sys
from pathlib import Path

from strategies.StochRsiMacdStrategy import *
from bot.training.genetic_trainer import GeneticTrainer

FILE_INDEX = 1
DATA_INDEX = 2


def __try_get_json_attr(key: str, json_obj):
    try:
        val = json_obj[key]
        return val
    except KeyError:
        return None


if len(sys.argv) == 1 or sys.argv[1] == "-h":
    print("train-genetic <options_file_path> <dataset_folder> -result_file_path-")
    sys.exit(0)

if len(sys.argv) < 3:
    print("Wrong parameters see usage with -h")
    sys.exit()

with open(sys.argv[FILE_INDEX]) as file:
    data = json.load(file)

result_path = ""
if len(sys.argv) > 3:
    result_path = sys.argv[3]

dataset_folder = sys.argv[DATA_INDEX]
strategy_name = data["strategy"]
strategy_class = getattr(importlib.import_module("strategies." + strategy_name), strategy_name)
genome_constraints = [(e["lower_bound"], e["upper_bound"]) for e in data["parameters"]]
hyperparameters = data["hyperparameters"]
preferences = data["preferences"]
result_path = "train-" + strategy_name + ".rep" if result_path == "" else result_path
if __name__ == '__main__':
    res = GeneticTrainer.train(strategy_class, genome_constraints, dataset_folder,
                               crossover_operator = __try_get_json_attr("crossover_operator", hyperparameters),
                               crossover_rate = __try_get_json_attr("crossover_rate", hyperparameters),
                               mutation_type = __try_get_json_attr("mutation_type", hyperparameters),
                               mutation_rate = __try_get_json_attr("mutation_rate", hyperparameters),
                               population_number = __try_get_json_attr("population_number", hyperparameters),
                               processes_number = __try_get_json_attr("processes_number", hyperparameters),
                               max_iterations = __try_get_json_attr("max_iterations", hyperparameters),
                               epoch_champion_report = __try_get_json_attr("epoch_champion_report", preferences),
                               data_delimiter = __try_get_json_attr("data_delimiter", preferences))
    with open(result_path, "w") as outfile: outfile.write(res.to_json())
