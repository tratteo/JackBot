import json

# data = pd.read_csv('09_2020_data.csv')
from numpy import genfromtxt

from Core.WalletDelegates import WalletDelegates
from Strategies.StochRsiMacdStrategy import StochRsiMacdStrategy


data = genfromtxt('09_2020_data.csv', delimiter=',')

CANDLE_TIME = 5
time = 0

mess = {
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

balance = 600


def change_balance(amount):
    global balance
    balance += amount


def get_balance():
    return balance


# dati di default
high = data[time, 2]
low = data[time, 3]
start_time = 0
highs = []
lows = []
closes = []

wallet = WalletDelegates(change_balance, get_balance)
strat = StochRsiMacdStrategy(wallet, True)
time_span = 36000
while time < time_span:  # len(data) -1:
    mess["k"]["c"] = str(data[time, 4])
    mess["k"]["h"] = str(data[time, 2])
    mess["k"]["l"] = str(data[time, 3])
    mess["k"]["t"] = str(data[time, 0])
    mess["k"]["T"] = str(data[time, 6])
    if high < data[time, 2]:
        high = data[time, 2]

    if low > data[time, 3]:
        low = data[time, 3]

    if time != 0 and (time % CANDLE_TIME) == CANDLE_TIME - 1:
        mess["k"]["x"] = True
        mess["k"]["h"] = str(high)
        mess["k"]["l"] = str(low)
        mess["k"]["t"] = start_time
        mess["k"]["T"] = data[time, 6]
        highs.append(float(mess["k"]["h"]))
        lows.append(float(mess["k"]["l"]))
        closes.append(float(mess["k"]["c"]))
        if time + 1 < len(data):
            high = data[time + 1, 2]  # setto i dati default alla prima candelotta aperta
            low = data[time + 1, 3]
            start_time = data[time + 1, 0]
        else:
            break

        strat.update_state(mess)
        # print("\n 5 min candle: " + str(mess))
        # print("RSI: " + str(rsi[-1]) + ", STOCH: " + str(stoch_k[-1]) + ", " + str(stoch_d[-1]) + ", MACD: " + str(macd[-1]) + ", " + str(signal[-1]))

    else:
        mess["k"]["x"] = False
    out = json.dumps(mess)
    # print(out)
    time += 1

for p in strat.open_positions:
    wallet.change_balance_delegate(p.investment)

percentage = 0
total_profit = 0
won = 0
days = time_span / 1440
for c in strat.closed_positions:
    percentage += c.result_percentage
    total_profit += c.profit
    if c.won: won += 1
win_percentage = 0
if len(strat.closed_positions) > 0:
    win_percentage = won / len(strat.closed_positions)

    # apy = ((((((((Core.Strategy.Strategy.INITIAL_BALANCE + total_profit) / Core.Strategy.Strategy.INITIAL_BALANCE) - 1) * 100) / days) / 100) + 1) ** 365 - 1) * 100
    # print("\nApy: " + str(apy) + "%")
    # print("Win percentage: " + str(win_percentage * 100))
print("Total profit: " + str(total_profit))
# print("Time span: " + str(days) + " days")
print("Final balance: " + str(wallet.get_balance_delegate()))
