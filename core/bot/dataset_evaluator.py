import numpy

from core.bot.middleware.data_frame import DataFrame
from core.bot.strategy import Strategy
from core.bot.test_result import TestResult
from core.bot.wallet_handler import TestWallet

OPEN_T: int = 0
HIGH: int = 2
LOW: int = 3
CLOSE: int = 4
CLOSE_T: int = 6




def evaluate(strategy: Strategy, initial_balance: float, data: numpy.ndarray, progress_delegate = None, balance_update_interval: int = 1440, timeframe: int = 3, index: int = 0) -> [
    TestResult,
    list[float],
    int]:

    epoch = 0
    high = data[epoch, HIGH]
    low = data[epoch, LOW]
    start_time = 0
    time_span = len(data)
    balance_trend = []
    frame = DataFrame()

    if not isinstance(strategy.wallet_handler, TestWallet):
        print("Unable to test the strategy, the wallet handler is not an instance of a TestWallet")
        return None, balance_trend, index

    # Report progress each month
    progress_reporter_span = 1440 * 30
    try:
        while epoch < time_span:
            if epoch + 1 >= len(data): break
            frame.close_price = str(data[epoch, CLOSE])
            frame.high_price = str(data[epoch, HIGH])
            frame.low_price = str(data[epoch, LOW])
            frame.start_time = str(data[epoch, OPEN_T])
            frame.close_time = str(data[epoch, CLOSE_T])
            frame.is_closed = False

            if high < data[epoch, HIGH]:
                high = data[epoch, HIGH]

            if low > data[epoch, LOW]:
                low = data[epoch, LOW]

            if epoch != 0 and (epoch % timeframe) == timeframe - 1:
                frame.is_closed = True
                frame.high_price = str(high)
                frame.low_price = str(low)
                frame.start_time = start_time
                frame.close_time = data[epoch, CLOSE_T]

                # Set defaults to next candle
                high = data[epoch + 1, 2]
                low = data[epoch + 1, 3]
                start_time = data[epoch + 1, 0]
            if epoch % balance_update_interval == 0: balance_trend.append(strategy.wallet_handler.get_balance())
              
            strategy.update_state(frame)
            if epoch % progress_reporter_span == 0 and progress_delegate is not None:
                progress_delegate(progress_reporter_span)

            epoch += 1
    except (KeyboardInterrupt, SystemExit):
        print("\nWorker " + str(index) + " interrupted", flush=True)
        # for p in strategy.open_positions:
        #     strategy.wallet_handler.balance += p.investment
        return None, balance_trend, index

    if progress_delegate is not None: progress_delegate(time_span - epoch)

    # for p in strategy.open_positions:
    #   strategy.wallet_handler.balance += p.investment

    balance_trend.append(strategy.wallet_handler.get_balance())
    res = TestResult(strategy, initial_balance, len(data), timeframe)
    return res, balance_trend, index
