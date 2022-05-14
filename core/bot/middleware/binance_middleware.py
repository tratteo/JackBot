from binance import ThreadedWebsocketManager
from core.bot.middleware.data_frame import DataFrame
from core.bot.middleware.middleware import MiddleWare


class BinanceMiddleWare(MiddleWare):
    def __init__(self, callback, symbol, granularity):
        super().__init__(callback, symbol, granularity)
        #insert key
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