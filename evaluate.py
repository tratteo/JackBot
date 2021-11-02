import importlib
import sys

import matplotlib.pyplot as plot
import talib
from numpy import genfromtxt

from bot import dataset_evaluator
from bot import lib
from bot.command.command_handler import CommandHandler
from bot.lib import ProgressBar
from strategies.StochRsiMacdStrategy import *


def helper(helper_str: str):
    print(helper_str, flush = True)
    exit(0)


def failure(helper_str: str):
    print("Wrong syntax \n")
    print(helper_str, flush = True)
    exit(1)


command_manager = CommandHandler.create() \
    .positional("Strategy file") \
    .positional("Dataset file") \
    .keyed("-o", "Output file .res") \
    .keyed("-p", "Plot balance with a certain precision") \
    .keyed("-ib", "The initial balance") \
    .on_help(helper) \
    .on_fail(failure) \
    .build(sys.argv)

with open(command_manager.get_p(0)) as file:
    options_file = json.load(file)

# Get args
initial_balance = int(command_manager.get_k("-ib"))
if initial_balance is None: initial_balance = 10000

plot_arg = lib.get_minutes_from_flag(command_manager.get_k("-p"))
balance_plot_interval = plot_arg
if balance_plot_interval is None: balance_plot_interval = 1440

dataset = command_manager.get_p(1)
timeframe = lib.get_minutes_from_flag(options_file["timeframe"])
out = command_manager.get_k("-o")

# Instantiate the strategy
strategy_name = options_file["strategy"]
strategy_class = getattr(importlib.import_module(config.DEFAULT_STRATEGIES_FOLDER + "." + strategy_name), strategy_name)
strategy = strategy_class(TestWallet.factory(initial_balance), *options_file["parameters"])

# Load data
print("Loading " + dataset + "...")
data = genfromtxt(dataset, delimiter = config.DEFAULT_DELIMITER)

# Evaluate
print("Evaluating " + strategy_name + " on " + dataset + " | " + str(options_file["timeframe"]))
progress_bar = ProgressBar.create(len(data)).width(50).build()
res, balance, index = dataset_evaluator.evaluate(strategy, initial_balance, data, progress_delegate = progress_bar.step, balance_update_interval = balance_plot_interval, timeframe = timeframe)
progress_bar.dispose()
print(str(res))

# Print to file
if out is not None:
    lib.create_folders_in_path(out, lambda: sys.exit(1))
    with open(out, "w") as file:
        file.write(str(res))

# Plot data
if plot_arg is not None:
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
    step = (balance_max - balance_min) / 10 if (balance_max - balance_min) / 10 > 1 else 1
    plot.yticks(np.arange(start = balance_min, stop = balance_max, step = step))
    plot.grid()
    plot.show()
