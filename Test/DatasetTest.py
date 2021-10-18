import sys

import tqdm
from numpy import genfromtxt

from Strategies.StochRsiMacdStrategy import *

data = genfromtxt('../Data/ETHUSDT_1-6_2021.csv', delimiter=';')

CANDLE_TIME = 5
INITIAL_BALANCE = 1000
TEST_DAYS = 180

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


def change_balance(amount):
    global balance
    balance += amount


def get_balance():
    return balance


# defaults data
epoch = 0
balance = INITIAL_BALANCE
high = data[epoch, HIGH]
low = data[epoch, LOW]
start_time = 0
time_span = TEST_DAYS * 1440
highs = []
lows = []
closes = []

strategy = StochRsiMacdStrategy(get_balance, True, change_balance)


# region Functions


def evaluate_performance():
    for p in strategy.open_positions:
        change_balance(p.investment)

    total_profit = 0
    won = 0
    days = time_span / 1440
    for c in strategy.closed_positions:
        total_profit += c.profit
        if c.won: won += 1
    win_percentage = 0
    if len(strategy.closed_positions) > 0:
        win_percentage = won / len(strategy.closed_positions)

    apy = ((((((((get_balance()) / INITIAL_BALANCE) - 1) * 100) / days) / 100) + 1) ** 365 - 1) * 100
    print("{:<20s}{:^4s}".format("Time span: ", str(int(days)) + " days"))
    print("{:<20s}{:^4.3f}".format("Initial balance: ", INITIAL_BALANCE))
    print("{:<20s}{:^4.3f}".format("Final balance: ", get_balance()))
    print("{:<20s}{:^4.3f}".format("Total profit: ", total_profit))
    print("{:<20s}{:^4.3s}".format("Opened positions: ", str(len(strategy.open_positions) + len(strategy.closed_positions))))
    print("{:<20s}{:^4.3f}".format("Win rate: ", win_percentage * 100) + "%")
    print("{:<20s}{:^4.3f}".format("Apy: ", apy) + "%")


# endregion

print("Processing data\n")
with tqdm.tqdm(total=time_span, unit="candles", file=sys.stdout) as bar:
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

        if epoch != 0 and (epoch % CANDLE_TIME) == CANDLE_TIME - 1:
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
        bar.update(1)

        epoch += 1

evaluate_performance()
