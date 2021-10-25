import importlib
import sys

from numpy import genfromtxt

from bot import dataset_evaluator
from strategies.StochRsiMacdStrategy import *

FILE_INDEX = 1
DATA_INDEX = 2


def __try_get_json_attr(key: str, json_obj):
    try:
        val = json_obj[key]
        return val
    except KeyError:
        return None


if len(sys.argv) < 3:
    print("Few arguments")
    sys.exit(1)

if sys.argv[2] == "-h":
    print("evaluate <strategy_file_path> <dataset_path>")
    sys.exit(0)
if len(sys.argv) < 3:
    print("Wrong parameters, see usage with -h")
    sys.exit()

with open(sys.argv[FILE_INDEX]) as file:
    data = json.load(file)

dataset = sys.argv[DATA_INDEX]
strategy_name = data["strategy"]
strategy_class = getattr(importlib.import_module("strategies." + strategy_name), strategy_name)
strategy = strategy_class(TestWallet.factory(), *data["parameters"])
print("Evaluating...")
res, index = DatasetEvaluator.evaluate(strategy, 1000, genfromtxt(dataset, delimiter = ';'), None)
print(res)
