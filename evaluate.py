import importlib
import sys
import config
from bot import lib
from numpy import genfromtxt

from bot import dataset_evaluator
from bot.command.command_handler import CommandHandler
from bot.lib import ProgressBar
from strategies.StochRsiMacdStrategy import *


def __try_get_json_attr(key: str, json_obj):
    try:
        val = json_obj[key]
        return val
    except KeyError:
        return None


def helper(helper_str: str):
    print(helper_str, flush = True)
    exit(0)


def failure(helper_str: str):
    print('Wrong syntax \n')
    print(helper_str, flush = True)
    exit(1)


command_manager = CommandHandler.create() \
    .positional('Strategy file') \
    .positional('Dataset file') \
    .keyed('-o', 'Output file .res') \
    .on_help(helper) \
    .on_fail(failure) \
    .build(sys.argv)

with open(command_manager.get_p(0)) as file:
    data = json.load(file)

dataset = command_manager.get_p(1)
strategy_name = data["strategy"]
strategy_class = getattr(importlib.import_module(config.DEFAULT_STRATEGIES_FOLDER + "." + strategy_name), strategy_name)
strategy = strategy_class(TestWallet.factory(), *data["parameters"])
print("Loading " + dataset + "...")
data = genfromtxt(dataset, delimiter = config.DEFAULT_DELIMITER)
print("Evaluating...")
progress_bar = ProgressBar.create(len(data)).width(50).build()
res, index = dataset_evaluator.evaluate(strategy, 1000, data, progress_report = progress_bar.step)
progress_bar.dispose()
print(res)
out = command_manager.get_k('-o')
if out is not None:
    lib.create_folders_in_path(out, lambda: sys.exit(1))
    with open(out, 'w') as file:
        file.write(str(res))
