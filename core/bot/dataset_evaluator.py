import numpy

from core.bot.strategy import Strategy
from core.bot.test_result import TestResult
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


def evaluate(strategy: Strategy, initial_balance: float, data: numpy.ndarray, progress_delegate = None, balance_update_interval: int = 1440, timeframe: int = 3, index: int = 0) -> [TestResult,
                                                                                                                                                                                     list[float],
                                                                                                                                                                                     int]:
    epoch = 0
    high = data[epoch, HIGH]
    low = data[epoch, LOW]
    start_time = 0
    time_span = len(data)
    balance_trend = []
    if not isinstance(strategy.wallet_handler, TestWallet):
        print("Unable to test the strategy, the wallet handler is not an instance of a TestWallet")
        return None, balance_trend, index

    # Report progress each month
    progress_reporter_span = 1440 * 30
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
        # for p in strategy.open_positions:
        #     strategy.wallet_handler.balance += p.investment
        return None, balance_trend, index

    if progress_delegate is not None: progress_delegate(time_span - epoch)

    # for p in strategy.open_positions:
    #   strategy.wallet_handler.balance += p.investment

    balance_trend.append(strategy.wallet_handler.get_balance())
    res = TestResult(strategy, initial_balance, len(data), timeframe)
    return res, balance_trend, index
