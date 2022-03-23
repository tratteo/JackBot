import threading
import time
from abc import abstractmethod, ABC
import config
from binance import ThreadedWebsocketManager

from CexLib.Kucoin.KucoinData import KucoinData
from core.bot.data_frame import DataFrame


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


class BinanceMiddleWare(MiddleWare):
    def __init__(self, callback, symbol, granularity):
        super().__init__(callback, symbol, granularity)
        self.twm = ThreadedWebsocketManager(api_key=config.API_KEY, api_secret=config.API_SECRET)
        self.twm.start()
        self.twm.start_kline_socket(callback=self.update, symbol=self.symbol)

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

    def update(self, message):
        self.callback(self.convert(message))

    def stop(self):
        self.twm.stop()


class KucoinMiddleWare(MiddleWare):

    def __init__(self, callback, symbol, granularity):
        super().__init__(callback, symbol, granularity)
        self.passed_frame = DataFrame()
        self.unsubscribe = True
        self.kucoin_data = KucoinData('key', 'secret', 'apiName')
        threading.Thread(target=self.subscribe).start()

    def subscribe(self):
        while self.unsubscribe:
            self.update(self.kucoin_data.get_candles(self.symbol, self.granularity))
            time.sleep(int(self.granularity) * 60)

    def convert(self, message) -> DataFrame:
        frame = DataFrame()
        frame.symbol = self.symbol
        frame.start_time = message[198][0]
        frame.close_time = message[198][0] + (int(self.granularity) * 60000)
        frame.open_price = message[198][1]
        frame.close_price = message[198][4]
        frame.high_price = message[198][2]
        frame.low_price = message[198][3]
        frame.is_closed = True
        return frame

    def stop(self):
        self.unsubscribe = False

    def update(self, message):
        self.callback(self.convert(message))

