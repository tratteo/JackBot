from abc import abstractmethod, ABC
import config
import os
from binance.client import Client
from kucoin.client import Client as Client_K
# from kucoin_futures.client import Trade
# from kucoin_futures.client import Market
from CexLib.Kucoin.KucoinOrder import Trade
from CexLib.Kucoin.KucoinData import Data



class WalletHandler(ABC):

    @abstractmethod
    def get_balance(self):
        pass


class KucoinWallet_spot(WalletHandler):

    def __init__(self,  api_key: str, api_secret: str, api_pass: str):
        super().__init__()
        self.client = Client_K(api_key, api_secret, api_pass, sandbox=False)


    def get_balance(self):
        balance = {'margin': 0, 'trade': 0, 'main': 0, 'futures': 0}
        prices = {}
        for accounts in self.client.get_accounts():
            asset = accounts['currency'] + '-USDT'
            if asset != 'USDT-USDT' and float(accounts['balance']) > 0:
                if asset not in prices:
                    prices[asset] = self.client.get_ticker(asset)['price']
                balance[accounts['type']] += float(accounts['balance']) * float(prices[asset])
            else:
                balance[accounts['type']] += float(accounts['balance'])

        print('------------------ACCOUNT BALANCE -----------------------')
        print('margin balance ' + str(balance['margin']) + ' USDT')
        print('spot balance ' + str(balance['trade']) + ' USDT')
        print('main balance ' + str(balance['main']) + ' USDT')
        print('futures balance ' + str(balance['futures']) + ' USDT')



class KucoinWallet_future(WalletHandler):
    def __init__(self,  api_key: str, api_secret: str, api_pass: str):
        super().__init__()
        self.trade = Trade(key=api_key, secret=api_secret, passphrase=api_pass, is_sandbox=False)
        self.data = Data(key=api_key, secret=api_secret, passphrase=api_pass, is_sandbox=False)

    def get_balance(self): # doesn't count positions
        return self.data.get_account_overview()['availableAmount']



class BinanceWallet(WalletHandler):

    def __init__(self, api_key: str, api_secret: str, api_url: str = "https://testnet.binancefuture.com"):
        super().__init__()
        self.client = Client(api_key, api_secret)
        self.client.API_URL = api_url

    def spot_balance(self):
        sum_btc = 0.0
        balances = self.client.get_account()
        for _balance in balances["balances"]:
            asset = _balance["asset"]
            if float(_balance["free"]) != 0.0 or float(_balance["locked"]) != 0.0:
                try:
                    btc_quantity = float(_balance["free"]) + float(_balance["locked"])
                    if asset == "BTC":
                        sum_btc += btc_quantity
                    else:
                        _price = self.client.get_symbol_ticker(symbol=asset + "BTC")
                        sum_btc += btc_quantity * float(_price["price"])
                except:
                    pass

        current_btc_price_USD = self.client.get_symbol_ticker(symbol="BTCUSDT")["price"]
        own_usd = sum_btc * float(current_btc_price_USD)
        print('------------------ACCOUNT BALANCE -----------------------')
        print('spot balance ' + str(own_usd) + ' USDT')




class TestWallet(WalletHandler):

    @classmethod
    def factory(cls, initial_balance: float):
        return TestWallet(initial_balance)

    def __init__(self, initial_balance: float):
        super().__init__()
        self.__balance = initial_balance
        self.balance_trend = [initial_balance]

    @property
    def balance(self):
        return self.__balance

    def get_balance(self) -> float:
        return self.balance

    @balance.setter
    def balance(self, value: float):  # setter privato
        self.__balance = value


if __name__ == "__main__":

    wallet = KucoinWallet_future(os.environ.get('FK_KEY'), os.environ.get('FK_SECRET'), os.environ.get('FK_PASS'))
    print(wallet.get_balance())
