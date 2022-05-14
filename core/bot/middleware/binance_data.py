from core.bot.middleware.data_frame import DataFrame


class BinanceData:

    def __init__(self):
        self.frame = DataFrame()

    def convert(self, message) -> DataFrame:
        self.frame.start_time = message["k"]["t"]
        self.frame.close_time = message["k"]["T"]
        self.frame.open_price = message["k"]["o"]
        self.frame.close_price = message["k"]["c"]
        self.frame.high_price = message["k"]["h"]
        self.frame.low_price = message["k"]["l"]
        self.frame.is_closed = message["k"]["x"]
        return self.frame
