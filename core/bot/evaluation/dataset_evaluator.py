import numpy

from core.bot.evaluation.test_result import EvaluationResult
from core.bot.logic.strategy import Strategy
from core.bot.logic.wallet_handler import TestWallet
from core.bot.middleware.data_frame import DataFrame

OPEN_T: int = 0
HIGH: int = 2
LOW: int = 3
CLOSE: int = 4
CLOSE_T: int = 6


def evaluate(strategy: Strategy, initial_balance: float, data: numpy.ndarray, progress_delegate = None, balance_update_interval: int = 1440, timeframe: int = 3, index: int = 0) -> [EvaluationResult,
                                                                                                                                                                                     list[float], int]:
    """Evaluate the strategy in a dataset
      Returns:
        tuple[evaluation_result, balance_trend, worker_index]
    """

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
            if epoch + 1 >= len(data):
                break
            frame.close_price = float(data[epoch, CLOSE])
            frame.high_price = float(data[epoch, HIGH])
            frame.low_price = float(data[epoch, LOW])
            frame.start_time = int(data[epoch, OPEN_T])
            frame.close_time = int(data[epoch, CLOSE_T])
            frame.is_closed = False

            if high < frame.high_price:
                high = frame.high_price

            if low > frame.low_price:
                low = frame.low_price

            if epoch != 0 and (epoch % timeframe) == timeframe - 1:
                frame.is_closed = True
                frame.high_price = high
                frame.low_price = low
                frame.start_time = start_time
                frame.close_time = data[epoch, CLOSE_T]

                # Set defaults to next candle
                high = data[epoch + 1, HIGH]
                low = data[epoch + 1, LOW]
                start_time = data[epoch + 1, OPEN_T]
            if epoch % balance_update_interval == 0:
                balance_trend.append(strategy.wallet_handler.total_balance)

            strategy.update_state(frame)
            if epoch % progress_reporter_span == 0 and progress_delegate is not None:
                progress_delegate(progress_reporter_span)

            epoch += 1
    except (KeyboardInterrupt, SystemExit):
        print("\nWorker " + str(index) + " interrupted", flush = True)
        # for p in strategy.open_positions:
        #     strategy.wallet_handler.balance += p.investment
        return None, balance_trend, index
    finally:

        if progress_delegate is not None:
            progress_delegate(time_span - epoch)
        for p in strategy.open_positions:
            strategy.wallet_handler.balance += p.investment
        balance_trend.append(strategy.wallet_handler.get_balance())
        res = EvaluationResult(strategy, initial_balance, len(data), timeframe)
        return res, balance_trend, index
