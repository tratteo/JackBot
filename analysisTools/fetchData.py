import datetime

from CexLib.Kucoin.KucoinData import KucoinData
import csv
import config
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

date = '1 Mar, 2022'


def fetchBinance(start, end, client : Client, data:KucoinData):

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
            if end == '':
                klines = client.get_historical_klines(s, Client.KLINE_INTERVAL_5MINUTE, start)
            else:
                klines = client.get_historical_klines(s, Client.KLINE_INTERVAL_5MINUTE, start, end)
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


def fetchKucoin(start:datetime.datetime, end:datetime.datetime, data:KucoinData, granularity:int):
    symbols = data.get_all_symbols()

    for s in symbols:
        file = 'data1/' + s + str(granularity) + str(start) + str(end) + '.csv'
        data.get_history(s,granularity,start,end,save_csv=True,file=file)


if __name__ == "__main__":
    data = KucoinData(os.environ.get('FK_KEY'), os.environ.get('FK_SECRET'), os.environ.get('FK_PASS'))
    client = Client(config.API_KEY, config.API_SECRET)

    fetchKucoin(datetime.datetime(2022, 3, 14), datetime.datetime(2022, 3, 28), data, 30)
