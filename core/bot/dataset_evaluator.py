import copy

import numpy

from core import lib
from core.bot.strategy import Strategy
from core.bot.wallet_handler import TestWallet

OPEN_T: int = 0
HIGH: int = 2
LOW: int = 3
CLOSE: int = 4
CLOSE_T: int = 6

frame_message = {
    "e": "kline",
    "E": 123456789,
    "s": "REDACTED",
    "k": {
        "t": 123400000,
        "T": 123460000,
        "s": "REDACTED",
        "i": "1m",
        "f": 100,
        "L": 200,
        "o": "0.0010",
        "c": "close",
        "h": "high",
        "l": "low",
        "v": "1000",
        "n": 100,
        "x": "isClosed",
        "q": "1.0000",
        "V": "500",
        "Q": "0.500",
        "B": "123456"
    }
}


class TestResult:
    def __init__(self):
        self.closed_positions = []
        self.total_profit = 0
        self.days = 0
        self.win_ratio = 0
        self.estimated_apy = 0
        self.minutes = 0
        self.initial_balance = 0
        self.opened_positions = 0
        self.final_balance = 0
        self.time_frame_minutes = 0

    @classmethod
    def construct(cls, strategy: Strategy, initial_balance: float, minute_candles: int, time_frame_minutes: int):
        result = TestResult()
        result.initial_balance = initial_balance
        result.total_profit = 0
        result.minutes = minute_candles
        result.days = float(minute_candles) / 1440
        result.time_frame_minutes = time_frame_minutes
        result.closed_positions = copy.deepcopy(strategy.closed_positions)
        won = 0
        for c in result.closed_positions:
            result.total_profit += c.profit
            if c.won: won += 1
        result.win_ratio = 0
        result.final_balance = result.initial_balance + result.total_profit
        if len(strategy.closed_positions) > 0: result.win_ratio = won / len(strategy.closed_positions)
        # result.estimated_apy = (((((((result.final_balance / initial_balance) - 1) * 100) / result.days) / 100) + 1) ** 365 - 1) * 100
        result.estimated_apy = (365 / result.days) * ((result.final_balance / result.initial_balance) - 1) * 100
        result.opened_positions = len(strategy.open_positions) + len(strategy.closed_positions)
        return result

    def get_dict(self):
        dic = self.__dict__
        dic.pop("closed_positions", None)
        return dic

    def __str__(self):
        return "{:<25s}{:^4.2f}".format("Time span (d): ", self.days) + \
               "\n{:<25s}{:^4s}".format("Time frame: ", lib.get_flag_from_minutes(self.time_frame_minutes)) + \
               "\n{:<25s}{:^4.3f}".format("Initial balance: ", self.initial_balance) + \
               "\n{:<25s}{:^4.3f}".format("Final balance: ", self.final_balance) + \
               "\n{:<25s}{:^4.3f}".format("Total profit: ", self.total_profit) + \
               "\n{:<25s}{:^4}".format("Opened positions: ", self.opened_positions) + \
               "\n{:<25s}{:^4.3f}".format("Win rate: ", self.win_ratio * 100) + "%" + \
               "\n{:<25s}{:^4.3f}".format("Estimated apy: ", self.estimated_apy) + "%"


def evaluate(strategy: Strategy, initial_balance: float, data: numpy.ndarray, progress_delegate, balance_update_interval: int = 1440, timeframe: int = 3, index: int = 0) -> [TestResult, list[float], int]:
    epoch = 0
    high = data[epoch, HIGH]
    low = data[epoch, LOW]
    start_time = 0
    time_span = len(data)
    highs = []
    lows = []
    closes = []
    balance_trend = []
    if not isinstance(strategy.wallet_handler, TestWallet):
        print("Unable to test the strategy, the wallet handler is not an instance of a TestWallet")
        return None, balance_trend, index

    # Report progress each week
    progress_reporter_span = 1440 * 7
    try:
        while epoch < time_span:
            if epoch + 1 >= len(data): break
            frame_message["k"]["c"] = str(data[epoch, CLOSE])
            frame_message["k"]["h"] = str(data[epoch, HIGH])
            frame_message["k"]["l"] = str(data[epoch, LOW])
            frame_message["k"]["t"] = str(data[epoch, OPEN_T])
            frame_message["k"]["T"] = str(data[epoch, CLOSE_T])
            frame_message["k"]["x"] = False
            if high < data[epoch, HIGH]:
                high = data[epoch, HIGH]

            if low > data[epoch, LOW]:
                low = data[epoch, LOW]

            if epoch != 0 and (epoch % timeframe) == timeframe - 1:
                frame_message["k"]["x"] = True
                frame_message["k"]["h"] = str(high)
                frame_message["k"]["l"] = str(low)
                frame_message["k"]["t"] = start_time
                frame_message["k"]["T"] = data[epoch, CLOSE_T]
                highs.append(float(high))
                lows.append(float(low))
                closes.append(float(data[epoch, CLOSE]))

                # Set defaults to next candle
                high = data[epoch + 1, 2]
                low = data[epoch + 1, 3]
                start_time = data[epoch + 1, 0]
            if epoch % balance_update_interval == 0: balance_trend.append(strategy.wallet_handler.get_balance())
            strategy.update_state(frame_message)
            if epoch % progress_reporter_span == 0 and progress_delegate is not None: progress_delegate(progress_reporter_span)
            epoch += 1
    except (KeyboardInterrupt, SystemExit):
        print("\nWorker " + str(index) + " interrupted", flush = True)
        for p in strategy.open_positions:
            strategy.wallet_handler.balance += p.investment
        return None, balance_trend, index

    if progress_delegate is not None: progress_delegate(time_span - epoch)

    # for p in strategy.open_positions:
    #   strategy.wallet_handler.balance += p.investment

    balance_trend.append(strategy.wallet_handler.get_balance())
    res = TestResult.construct(strategy, initial_balance, len(data), timeframe)
    return res, balance_trend, index
