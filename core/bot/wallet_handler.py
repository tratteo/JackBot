from abc import abstractmethod, ABC

from binance.client import Client


class WalletHandler(ABC):

    @abstractmethod
    def get_balance(self) -> float:
        pass


class KucoinWallet(WalletHandler):

    @classmethod
    def factory(cls, options, api_key: str, api_secret: str, api_url: str):
        return KucoinWallet(options, api_key, api_secret, api_url)

    def __init__(self, options, api_key: str, api_secret: str, api_url: str):
        self.options = options
        self.client = Client(api_key, api_secret)
        self.client.API_URL = api_url

    def get_balance(self) -> float:
        pass


class BinanceWallet(WalletHandler):

    @classmethod
    def factory(cls, options, api_key: str, api_secret: str, api_url: str = "https://testnet.binance.vision/api"):
        return BinanceWallet(options, api_key, api_secret, api_url)

    def __init__(self, options, api_key: str, api_secret: str, api_url: str):
        self.options = options
        self.client = Client(api_key, api_secret)
        self.client.API_URL = api_url

    def get_balance(self) -> float:
        return float(self.client.get_asset_balance(asset = self.options["second"])["free"])

    def get_asset_balance(self) -> float:
        return float(self.client.get_asset_balance(asset = self.options["first"])["free"])


class TestWallet(WalletHandler):

    @classmethod
    def factory(cls, initial_balance: float):
        return TestWallet(initial_balance)

    def __init__(self, initial_balance: float):
        self.__balance = initial_balance

    @property
    def balance(self):
        return self.__balance

    def get_balance(self) -> float:
        return self.balance

    @balance.setter
    def balance(self, value: float):
        self.__balance = value
