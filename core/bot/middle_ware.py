from abc import abstractmethod, ABC

from kucoin.asyncio import KucoinSocketManager
from kucoin.client import Client

import config

from binance import ThreadedWebsocketManager


# {
#   "k": {
#     "t": 123400000, // Kline start time---
#     "T": 123460000, // Kline close time---
#     "o": "0.0010",  // Open price---
#     "c": "0.0020",  // Close price---
#     "h": "0.0025",  // High price---
#     "l": "0.0015",  // Low price---
#     "x": false,     // Is this kline closed?---
#   }
# }

class DataFrame(ABC):
    def __init__(self):
        self.start_time = 0
        self.close_time = 0
        self.open_price = 0
        self.close_price = 0
        self.high_price = 0
        self.low_price = 0
        self.is_closed = False


class MiddleWare(ABC):
    def __init__(self, callback):
        self.callback = callback

    @abstractmethod
    def convert(self, message) -> DataFrame:
        pass

    @abstractmethod
    def stop(self):
        pass

    def update(self, message):
        self.callback(self.convert(message))

    @classmethod
    def factory(cls, callback, env):
        if env == "binance":
            return BinanceMiddleWare(callback)


class BinanceMiddleWare(MiddleWare):
    def stop(self):
        self.twm.stop()
        pass

    def __init__(self, callback):
        super().__init__(callback)
        self.twm = ThreadedWebsocketManager(api_key=config.API_KEY, api_secret=config.API_SECRET)
        self.twm.start()
        self.twm.start_kline_socket(callback=self.update, symbol=options["first"] + options["second"])

    def convert(self, message) -> DataFrame:
        frame = DataFrame()
        frame.start_time = message["k"]["t"]
        frame.close_time = message["k"]["T"]
        frame.open_price = message["k"]["o"]
        frame.close_price = message["k"]["c"]
        frame.high_price = message["k"]["h"]
        frame.low_price = message["k"]["l"]
        frame.is_closed = message["k"]["x"]
        return frame


class KucoinMiddleWare(MiddleWare):
    def stop(self):
        self.twm.stop()
        pass

    def __init__(self, callback):
        super().__init__(callback)
        client = Client(api_key, api_secret, api_passphrase)

        ksm = await KucoinSocketManager.create(loop, client, handle_evt)
        await ksm.subscribe('/market/snapshot:BTC')

    def convert(self, message) -> DataFrame:
        frame = DataFrame()
        frame.start_time = message["k"]["t"]
        frame.close_time = message["k"]["T"]
        frame.open_price = message["k"]["o"]
        frame.close_price = message["k"]["c"]
        frame.high_price = message["k"]["h"]
        frame.low_price = message["k"]["l"]
        frame.is_closed = message["k"]["x"]
        return frame
