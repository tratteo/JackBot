import importlib
import json
import os
import json
import sys
from strategies.AtrSrsi3EmaStrategy import AtrSrsi3EmaStrategy

import config
from core.command_handler import CommandHandler
from core.bot.wallet_handler import KucoinWallet, BinanceWallet

API_KEY = "vTh6WDXyy9sojFQPT7Q615JX31oEEMGrLAexaadpS4V4vlhVDqqvF3mBwMXmVS8V"
API_SECRET = "nuC2xLmP1tWM8gJg59R5eAi0yJDQjnVST7hH0sSaKrKe4l81UF15pRc3y2UYHA1A"

options = {
  "first": "BTC",
  "second": "USDT"
}

# client = KucoinWallet.factory(config.KUCOIN_KEY, config.KUCOIN_SECRET, config.KUCOIN_PASS)
client = BinanceWallet.factory(options, API_KEY, API_SECRET)

client.get_balance()
# print(client.client.get_accounts())


