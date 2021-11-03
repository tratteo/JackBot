import sys
import importlib
import json
from bot import core
import time
import datetime
import config
from bot.command.command_handler import CommandHandler
from strategies.StochRsiMacdStrategy import *
from time import sleep
from binance import ThreadedWebsocketManager
import os


def update(msg):
    if msg['e'] != 'error':
        strategy.update_state(msg)
    else:
        print('error in reception')


def helper(helper_str: str):
    print(helper_str, flush=True)
    exit(0)


def failure(helper_str: str):
    print('Wrong syntax \n', flush=True)
    print(helper_str, flush=True)
    exit(1)


cmd = CommandHandler.create().positional("options").positional("strategy").on_fail(failure).on_help(helper).build(sys.argv)
clear = lambda: os.system('cls')

with open(cmd.get_p(0)) as file:
    options = json.load(file)

with open(cmd.get_p(1)) as file:
    data = json.load(file)

strategy_name = data["strategy"]
strategy_class = getattr(importlib.import_module("strategies." + strategy_name), strategy_name)
wallet = BinanceWallet(options, config.API_KEY, config.API_SECRET)
strategy = strategy_class(wallet, *data["parameters"])

twm = ThreadedWebsocketManager(api_key=config.API_KEY, api_secret=config.API_SECRET)
twm.start()
twm.start_kline_socket(callback=update, symbol=options["first"] + options["second"])

while True:
    inp = input()
    clear()
    if inp == 'balance':
        print(options["first"] , (wallet.get_asset_balance()))
        print(options["second"] , wallet.get_second_balance())

    elif inp == 'q':  # l'errore che genera può essere ignorato
        twm.stop()
        exit()

    else:
        print("invalid input")











