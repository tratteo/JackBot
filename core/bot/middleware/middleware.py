from abc import abstractmethod, ABC

from core.bot.middleware.binance_middleware import BinanceMiddleWare
from core.bot.middleware.kucoin_middleware import KucoinMiddleWare
from core.bot.middleware.data_frame import DataFrame


class MiddleWare(ABC):
    def __init__(self, callback, symbol, granularity):
        self.callback = callback
        self.symbol = symbol
        self.granularity = granularity

    @abstractmethod
    def convert(self, message) -> DataFrame:
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def update(self, message):
        pass

    @classmethod
    def factory(cls, callback, symbol, granularity, env):
        if env == "kucoin":
            return KucoinMiddleWare(callback, symbol, granularity)
        elif env == "binance":
            return BinanceMiddleWare(callback, symbol, granularity)
