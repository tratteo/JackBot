import sys
import importlib
import json
from bot import core
import datetime
import config
from strategies.StochRsiMacdStrategy import *
from time import sleep
from binance import ThreadedWebsocketManager


def update(msg):
    if msg['e'] != 'error':
        print(msg)
        strategy.update_state(msg)
    else:
        print('error in reception')


with open('run-options.json') as file:
    options = json.load(file)

if len(sys.argv) == 1 or sys.argv[1] == "-h":
    print("<strategy name>")
    sys.exit(0)

with open(sys.argv[1]) as file:
    data = json.load(file)

strategy_name = data["strategy"]
strategy_class = getattr(importlib.import_module("strategies." + strategy_name), strategy_name)
strategy = strategy_class(BinanceWallet(options, config.API_KEY, config.API_SECRET), *data["parameters"])

twm = ThreadedWebsocketManager(api_key = config.API_KEY, api_secret = config.API_SECRET)
twm.start()

try:
    twm.start_kline_socket(callback = update, symbol = 'BTCUSDT')
except:
    print('error')
    exit()

if input() == 'q':
    twm.stop()
