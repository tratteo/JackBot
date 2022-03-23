from CexLib.Kucoin.KucoinData import Data
import csv
import config
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

date = '1 Mar, 2022'

data = Data(os.environ.get('FK_KEY'), os.environ.get('FK_SECRET'), os.environ.get('FK_PASS'))
client = Client(config.API_KEY, config.API_SECRET)

symbols = []
for s in data.get_all_symbols():
    if s.endswith('M'):
        symbols.append(s[:-1])

klines = None
error = False
for s in symbols:
    file = 'data/' + s + "_5m_" + date + '.csv'
    print(s)
    try:
        klines = client.get_historical_klines(s, Client.KLINE_INTERVAL_5MINUTE, date)
    except BinanceAPIException:
        print('error', s)
        error = True
    # print(klines)

    if not error:
        print(file)

        with open(file, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(klines)

    error = False


