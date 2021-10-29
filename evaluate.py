import importlib
import sys
import config

from numpy import genfromtxt

from bot import dataset_evaluator
from bot.command.commandHandler import CommandHandler
from strategies.StochRsiMacdStrategy import *


def __try_get_json_attr(key: str, json_obj):
    try:
        val = json_obj[key]
        return val
    except KeyError:
        return None


def helper(helperstr: str):
    print(helperstr,flush=True)
    exit(0)

def failure(helperstr: str):
    print('Wrong synthax \n')
    print(helperstr,flush=True)
    exit(1)


command_manager = CommandHandler.create() \
    .positional('Strategy file') \
    .positional('Dataset file') \
    .keyed('-o', 'Output file .res') \
    .on_help(helper)\
    .on_fail(failure) \
    .build(sys.argv)


with open(command_manager.get_p(0)) as file:
    data = json.load(file)

dataset = command_manager.get_p(1)
strategy_name = data["strategy"]
strategy_class = getattr(importlib.import_module("strategies." + strategy_name), strategy_name)
strategy = strategy_class(TestWallet.factory(), *data["parameters"])
print("Evaluating...")
res, index = dataset_evaluator.evaluate(strategy, 1000, genfromtxt(dataset, delimiter=config.DEFAULT_DELIMITER), None)
print(res)

out = command_manager.get_k('-o')

if out is not None:
    with open(out, 'w') as file:
        file.write(str(res))
