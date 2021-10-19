import sys

from numpy import genfromtxt
import tqdm
from Bot.Core import Strategy

OPEN_T: int = 0
HIGH: int = 2
LOW: int = 3
CLOSE: int = 4
CLOSE_T: int = 6

frame_message = {
    "e": "kline",
    "E": 123456789,
    "s": "BNBBTC",
    "k": {
        "t": 123400000,
        "T": 123460000,
        "s": "BNBBTC",
        "i": "1m",
        "f": 100,
        "L": 200,
        "o": "0.0010",
        "c": "close",
        "h": "high",
        "l": "low",
        "v": "1000",
        "n": 100,
        "x": 'isClosed',
        "q": "1.0000",
        "V": "500",
        "Q": "0.500",
        "B": "123456"
    }
}


class TestResult:
    def __init__(self):
        self.total_profit = 0
        self.days = 0
        self.win_percentage = 0
        self.apy = 0
        self.final_balance = 0
        self.opened_positions = 0

    @classmethod
    def construct(cls, strategy: Strategy, initial_balance: float, minute_candles: int):
        result = TestResult()
        result.total_profit = 0
        result.days = minute_candles / 1440
        won = 0
        for c in strategy.closed_positions:
            result.total_profit += c.profit
            if c.won: won += 1
        result.win_percentage = 0
        if len(strategy.closed_positions) > 0:
            result.win_percentage = won / len(strategy.closed_positions)
        result.apy = ((((((((strategy.get_balance_delegate()) / initial_balance) - 1) * 100) / result.days) / 100) + 1) ** 365 - 1) * 100
        result.final_balance = strategy.get_balance_delegate()
        result.opened_positions = len(strategy.open_positions) + len(strategy.closed_positions)
        return result

    def __str__(self):
        return "{:<20s}{:^4s}".format("Time span: ", str(int(self.days)) + " days") + \
               "\n{:<20s}{:^4.3f}".format("Initial balance: ", self.final_balance - self.total_profit) + \
               "\n{:<20s}{:^4.3f}".format("Final balance: ", self.final_balance) + \
               "\n{:<20s}{:^4.3f}".format("Total profit: ", self.total_profit) + \
               "\n{:<20s}{:^4.3s}".format("Opened positions: ", str(self.opened_positions)) + \
               "\n{:<20s}{:^4.3f}".format("Win rate: ", self.win_percentage * 100) + "%" + \
               "\n{:<20s}{:^4.3f}".format("Apy: ", self.apy) + "%"


def evaluate(strategy_class, initial_balance: float, data, verbose: bool = False, index: int = 0) -> TestResult:
    balance = initial_balance

    def change_balance(amount):
        nonlocal balance
        balance += amount

    def get_balance():
        return balance

    candle_time = 5
    epoch = 0
    high = data[epoch, HIGH]
    low = data[epoch, LOW]
    start_time = 0
    time_span = len(data)
    highs = []
    lows = []
    closes = []

    strategy = strategy_class(get_balance, True, change_balance)

    if verbose: print("[" + str(index) + "] Processing data\n")
    # with tqdm.tqdm(total = time_span, unit = "candles", file = sys.stdout) as bar:
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

        if epoch != 0 and (epoch % candle_time) == candle_time - 1:
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

        strategy.update_state(frame_message)
        # if verbose: print(str(index) + ": " + str(epoch / time_span))
        # bar.update(1)

        epoch += 1

    for p in strategy.open_positions:
        change_balance(p.investment)

    res = TestResult.construct(strategy, initial_balance, len(data))
    return res
