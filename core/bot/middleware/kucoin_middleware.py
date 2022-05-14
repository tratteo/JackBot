import threading
import time

from core.bot.middleware.data_frame import DataFrame
from core.bot.middleware.middleware import MiddleWare


# from CexLib.Kucoin.KucoinData import KucoinData
# importare cartella da branch main/stefano/enrico

class KucoinMiddleWare(MiddleWare):

    def __init__(self, callback, symbol, granularity):
        super().__init__(callback, symbol, granularity)
        self.passed_frame = DataFrame()
        self.unsubscribe = True
        self.kucoin_data = KucoinData('key', 'secret', 'apiName')  # insert key to subscribe
        threading.Thread(target = self.subscribe).start()

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
