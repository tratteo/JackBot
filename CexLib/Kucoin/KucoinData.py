from CexLib.Kucoin.KucoinRequest import KucoinFuturesBaseRestApi
import os

class Data(KucoinFuturesBaseRestApi):

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

        return self._request('GET', '/api/v1/withdrawals/quotas', params=params)


if __name__ == "__main__":

    data = Data(os.environ.get('FKUCOIN_KEY'), os.environ.get('FKUCOIN_SECRET'), os.environ.get('FKUCOIN_PASS'))
    # for x in sorted(data.get_all_symbols()):
    #     print(x)

    print(data.get_account_overview())