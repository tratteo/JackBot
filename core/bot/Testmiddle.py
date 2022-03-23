import time

from core.bot.middle_ware import MiddleWare


def ciao(message):
    print("start time: " + str(message.start_time))
    print("close time: " + str(message.close_time))
    print("open price: " + str(message.open_price))
    print("close price: " + str(message.close_price))
    print("high price: " + str(message.high_price))
    print("low price: " + str(message.low_price))


def main():
    middle = MiddleWare.factory(ciao, 'XBTUSDTM', '1', 'kucoin')
    i = 0

    while 1:
        print('main')
        time.sleep(10)
        # if i == 10:
        #     middle.stop()
        #     print('thread spento')
        # i += 1


if __name__ == "__main__":
    main()
