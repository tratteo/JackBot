
import datetime
import time
import numpy as np
from CexLib.Kucoin.KucoinRequest import KucoinFuturesBaseRestApi
import os
import csv


class KucoinData(KucoinFuturesBaseRestApi):


    def __init__(self, key, secret, passphrase, is_sandbox=False, url='', is_v1api=False):
        super().__init__(key, secret, passphrase, is_sandbox, url, is_v1api)

    def get_current_mark_price(self, symbol):
        """
        https://docs.kumex.com/#get-current-mark-price
        :param symbol:
        :type: str
        :return: {'symbol': 'XBTUSDM', 'indexPrice': 8194.22, 'granularity': 5000, 'timePoint': 1570613025000, 'value': 8194.49}
        """

        return self._request('GET', '/api/v1/mark-price/{symbol}/current'.format(symbol=symbol), auth=False)

    def get_all_symbols(self):
        res = self._request('GET', '/api/v1/contracts/active')
        symbols = [i['symbol'] for i in res]
        return symbols

    def get_account_overview(self, currency='USDT'):
        """
        https://docs.kumex.com/#get-account-overview
        :return:
        {
          "accountEquity": 99.8999305281, //Account equity
          "unrealisedPNL": 0, //Unrealised profit and loss
          "marginBalance": 99.8999305281, //Margin balance
          "positionMargin": 0, //Position margin
          "orderMargin": 0, //Order margin
          "frozenFunds": 0, //Frozen funds for withdrawal and out-transfer
          "availableBalance": 99.8999305281 //Available balance
          "currency": "XBT" //currency code
        }
        """
        params = {
            'currency': currency
        }


        params = {
            'currency': currency
        }

        return self._request('GET', '/api/v1/withdrawals/quotas', params=params)

    def get_candles(self, symbol='XBTUSDTM', granularity='5'):
        params = {
            'symbol': symbol,
            'granularity': granularity,
        }
        return self._request('GET', '/api/v1/kline/query', params=params)

    def get_history(self, symbol, granularity, start_date: datetime.datetime, end_date: datetime.datetime, save_csv=False, file = ''):
        start = int(time.mktime(start_date.timetuple()) * 1000)
        end = int(time.mktime(end_date.timetuple()) * 1000)
        print('retrieving:', symbol)
        params = {
            'symbol': symbol,
            'granularity': granularity,
            'from': 1268305200000
        }

        first = self._request('GET', '/api/v1/kline/query', params=params)

        if start < int(first[0][0]):
            print('Data NOT availible before', datetime.datetime.utcfromtimestamp(first[0][0]/1000).strftime('%Y-%m-%d %H:%M:%S'), '(UNIX=',first[0][0], ')')
            start = int(first[0][0])

        data = []
        step = granularity * 60 * 1000 * 200
        finish = end

        for i in range(start, end, step):
            if end < i + step:
                finish = end
            else:
                finish = i + step

            params = {
                'symbol': symbol,
                'granularity': granularity,
                'from': i,
                'to': finish
            }

            data.extend(self._request('GET', '/api/v1/kline/query', params=params))
            print('retrieved until', datetime.datetime.utcfromtimestamp(finish/1000).strftime('%Y-%m-%d %H:%M '))

        if save_csv:

            with open(file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerows(data)

        return data




if __name__ == "__main__":
    data = KucoinData(os.environ.get('FK_KEY'), os.environ.get('FK_SECRET'), os.environ.get('FK_PASS'))

    # print(data._request('GET', '/api/v1/kline/query?symbol=XBTUSDTM&granularity=5&from=1268305200000'))
    # xbt = data.get_history('XBTUSDTM', 5, datetime.datetime(2021, 3, 15, 10), datetime.datetime(2022, 3, 16, 10), save_csv=True)
    # print(len(xbt))

    print(len(data.get_all_symbols()))

