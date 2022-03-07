import importlib
import json
import os
import sys

# from binance import ThreadedWebsocketManager

import config
from core.bot.middle_ware import MiddleWare
from core.command_handler import CommandHandler
from core.bot.wallet_handler import BinanceWallet


def update(msg):
    if msg["e"] != "error":
        strategy.update_state(msg)
    else:
        print("error in reception")


def helper(helper_str: str):
    print(helper_str, flush=True)
    exit(0)


def failure(helper_str: str):
    print("Wrong syntax \n", flush=True)
    print(helper_str, flush=True)
    exit(1)


def clear():
    os.system("cls")


cmd = CommandHandler.create().positional("env").positional("strategy").on_fail(failure).on_help(helper).build(sys.argv)

env = cmd.get_p(0)

with open(cmd.get_p(1)) as file:
    data = json.load(file)

strategy_name = data["strategy"]
strategy_class = getattr(importlib.import_module("strategies." + strategy_name), strategy_name)
wallet = BinanceWallet.factory(env, config.API_KEY, config.API_SECRET)  # walletHandlerFactory
strategy = strategy_class(wallet, *data["parameters"])

# twm = ThreadedWebsocketManager(api_key = config.API_KEY, api_secret = config.API_SECRET)
# twm.start()
# twm.start_kline_socket(callback = update, symbol = options["first"] + options["second"])

middleware = MiddleWare.factory(strategy.update_state, env)

while True:
    inp = input()
    clear()
    # if inp == "balance":
    #     print(options["first"], (wallet.get_asset_balance()))         #da cambiare
    #     print(options["second"], wallet.get_second_balance())

    # Error can be ignored
    # elif inp == "q":
    if inp == "q":
        middleware.stop()
        exit()

    else:
        print("invalid input")
