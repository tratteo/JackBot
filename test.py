import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *
import numpy as np
import time
from Indicators import Indicator

# https://data.binance.vision/?prefix=data

SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
RSI_PERIOD = 14
TRADE_SYMBOL = 'ETHUSDT'
TRADE_QUANTITY = 0.005

macds = []
closes = []
highs = []
lows = []



is_long = False
client = Client(config.API_KEY, config.API_SECRET)
hist = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_5MINUTE, "5 day ago UTC")

hist = hist[:-1]

print(np.array(hist).shape)


for a in hist:
    closes.append(float(a[4]))
    highs.append(float(a[2]))
    lows.append(float(a[3]))



print("Closes len: " + str(len(closes)))
print("Highs len: " + str(len(highs)))
print("Lows len: " + str(len(lows)))

print(closes[0])


np_closes = numpy.array(closes)
macd, signal, hist = talib.MACD(np_closes)
rsi = talib.RSI(np_closes, RSI_PERIOD)
stoch_k, stoch_d = talib.STOCH(numpy.array(highs), numpy.array(lows), np_closes, fastk_period=14,
                               slowk_period=1,
                               slowd_period=3, slowk_matype=0, slowd_matype=0)
print("Stochastic: [k, d] > [" + str(stoch_k[-1]) + ", " + str(stoch_d[-1]) + "]")
print("RSI: " + str(rsi[-1]))
print("MACD: [macd, sig] > [" + str(macd[-1]) + ", " + str(signal[-1]) + "]")




def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True


def on_open(ws):
    print('opened connection')


def on_close(ws):
    print('closed connection')


def can_long(rsi, macd, stoch):
    global is_long
    last_macd = macds[-1]
    stoch_k = stoch[0]
    stoch_d = stoch[1]
    if not is_long:
        if stoch_k[-1] < 20 and stoch_d[-1] < 20:
            is_long = True
    elif stoch_k[-1] > 80 or stoch_d[-1] > 80:
        is_long = False
        print("Cannot enter long, stoch not correct")

    print(is_long)
    if is_long:
        res = rsi > 50 and (macd[0] > macd[1] and last_macd[0] < last_macd[1])
        print("Returning: " + str(res))
        return res

    return False


def on_message_event(ws, message):
    json_message = json.loads(message)
    # pprint.pprint(json_message)
    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']
    if is_candle_closed:
        print("candle closed at {}".format(candle))
        closes.append(float(close))
        highs.append(float(candle['h']))
        lows.append(float(candle['l']))
        np_closes = numpy.array(closes)
        macd, signal, hist = talib.MACD(np_closes)

        rsi = talib.RSI(np_closes, RSI_PERIOD)
        stoch_k, stoch_d = talib.STOCH(numpy.array(highs), numpy.array(lows), np_closes, fastk_period=14,
                                       slowk_period=1,
                                       slowd_period=3, slowk_matype=0, slowd_matype=0)
        print("Stochastic: [k, d] > [" + str(stoch_k[-1]) + ", " + str(stoch_d[-1]) + "]")
        print("RSI: " + str(rsi[-1]))
        print("MACD: [macd, sig] > [" + str(macd[-1]) + ", " + str(signal[-1]) + "]")

        # print("checking")
        # can = can_long(rsi, [macd, signal], [stoch_k, stoch_d])
        # if can:
        #     print("Long entered")


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message_event)
ws.run_forever()
