import importlib
import sys

import matplotlib.pyplot as plot
import talib
from numpy import genfromtxt

import config
from bot import dataset_evaluator
from bot import lib
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
    .keyed("-p", "Plot balance with a certain precision") \
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
balance_plot_interval = 1440
plot_arg = command_manager.get_k("-p")
if plot_arg is not None:
    balance_plot_interval = lib.get_minutes_from_flag(plot_arg)
progress_bar = ProgressBar.create(len(data)).width(50).build()
res, balance, index = dataset_evaluator.evaluate(strategy, 1000, data, progress_delegate = progress_bar.step, balance_update_interval = balance_plot_interval)
progress_bar.dispose()
print(res)
out = command_manager.get_k('-o')
if out is not None:
    lib.create_folders_in_path(out, lambda: sys.exit(1))
    with open(out, 'w') as file:
        file.write(str(res))

if plot_arg is not None:
    # print([str(b) for b in balance])
    balance_ema = talib.MA(np.array(balance), timeperiod = 25)
    balance_min, balance_max = min(balance), max(balance)
    balance_len = len(balance)
    plot.figure(num = strategy_name)
    plot.plot(balance, label = "Balance")
    plot.plot(balance_ema, label = "EMA")
    plot.title(strategy_name + " on " + dataset)
    plot.ylabel("Balance")
    plot.xlabel(plot_arg)
    plot.legend()
    step = balance_len / 40 if balance_len > 80 else 1
    plot.xticks(np.arange(start = 0, stop = len(balance) + 1, step = int(step)))
    step = (balance_max - balance_min) / 5 if (balance_max - balance_min) / 4 > 25 else 25
    plot.yticks(np.arange(start = balance_min, stop = balance_max, step = step))
    plot.grid()
    plot.show()
