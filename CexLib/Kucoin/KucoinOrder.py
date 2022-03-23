from CexLib.Kucoin.KucoinRequest import KucoinFuturesBaseRestApi
import os

class Trade(KucoinFuturesBaseRestApi):

    def __init__(self, key, secret, passphrase, is_sandbox=False, url='', is_v1api=False):
        super().__init__(key, secret, passphrase, is_sandbox, url, is_v1api)

    def get_all_position(self):
        """
        https://docs.kumex.com/#get-position-list
        :return:
        [{
          "id": "5ce3cda60c19fc0d4e9ae7cd",                //Position ID
          "symbol": "XBTUSDM",                              //Symbol
          "autoDeposit": true,                             //Auto deposit margin or not
          "maintMarginReq": 0.005,                         //Maintenance margin requirement
          "riskLimit": 200,                                //Risk limit
          "realLeverage": 1.06,                            //Leverage of the order
          "crossMode": false,                              //Cross mode or not
          "delevPercentage": 0.1,                          //ADL ranking percentile
          "openingTimestamp": 1558433191000,               //Open time
          "currentTimestamp": 1558507727807,               //Current timestamp
          "currentQty": -20,                               //Current position
          "currentCost": 0.00266375,                       //Current position value
          "currentComm": 0.00000271,                       //Current commission
          "unrealisedCost": 0.00266375,                    //Unrealised value
          "realisedGrossCost": 0,                          //Accumulated realised gross profit value
          "realisedCost": 0.00000271,                      //Current realised position value
          "isOpen": true,                                  //Opened position or not
          "markPrice": 7933.01,                            //Mark price
          "markValue": 0.00252111,                         //Mark value
          "posCost": 0.00266375,                           //Position value
          "posCross": 1.2e-7,                              //Manually added margin
          "posInit": 0.00266375,                           //Leverage margin
          "posComm": 0.00000392,                           //Bankruptcy cost
          "posLoss": 0,                                    //Funding fees paid out
          "posMargin": 0.00266779,                         //Position margin
          "posMaint": 0.00001724,                          //Maintenance margin
          "maintMargin": 0.00252516,                       //Position margin
          "realisedGrossPnl": 0,                           //Accumulated realised gross profit value
          "realisedPnl": -0.00000253,                      //Realised profit and loss
          "unrealisedPnl": -0.00014264,                    //Unrealised profit and loss
          "unrealisedPnlPcnt": -0.0535,                    //Profit-loss ratio of the position
          "unrealisedRoePcnt": -0.0535,                    //Rate of return on investment
          "avgEntryPrice": 7508.22,                        //Average entry price
          "liquidationPrice": 1000000,                     //Liquidation price
          "bankruptPrice": 1000000                         //Bankruptcy price
          "settleCurrency": "XBT"                         //Currency used to clear and settle the trades
        },
        ....]
        """
        print('inside ', self.key, 'end')
        return self._request('GET', '/api/v1/positions')

    def create_market_order(self, symbol, side, lever, size, clientOid='', **kwargs):
        """
        Place Limit Order Functions
        https://docs.kumex.com/#place-an-order
        :param symbol: interest symbol (Mandatory)
        :type: str
        :param side: place direction buy or sell (Mandatory)
        :type: str
        :param lever: Leverage of the order (Mandatory)
        :type: str
        :param size: Order size. Must be a positive number (Mandatory)
        :type: integer
        :param clientOid: Unique order id created by users to identify their orders, e.g. UUID, Only allows numbers,
         characters, underline(_), and separator(-) (Mandatory)
        :type: str
        :param kwargs:  Fill in parameters with reference documents
        :return: {'orderId': '5d9ee461f24b80689797fd04'}
        """
        stop = 'up'
        if side == 'buy':
            stop = 'down'

        params = {
            'symbol': symbol,
            'size': size,
            'side': side,
            'leverage': lever,
            'type': 'market'
        }

        if not clientOid:
            clientOid = self.return_unique_id
        params['clientOid'] = clientOid
        if kwargs:
            params.update(kwargs)

        return self._request('POST', '/api/v1/orders', params=params)

    def TPSL(self, symbol, side, lever, size, take_profit, stop_loss, clientOid='', **kwargs):

        stop = ''

        if side == 'buy':
            stop = 'down'
            side = 'sell'
        else:
            side = 'buy'
            stop = 'up'


        params = {
            'symbol': symbol,
            'price': take_profit,
            'size': size,
            'side': side,
            'leverage': lever,
            'stop': stop,
            'stopPriceType': 'MP',
            'stopPrice': stop_loss,
            'type': 'limit'
        }

        if not clientOid:
            clientOid = self.return_unique_id
        params['clientOid'] = clientOid
        if kwargs:
            params.update(kwargs)

        return self._request('POST', '/api/v1/orders', params=params)


if __name__ == "__main__":
    trade = Trade(os.environ.get('FKUCOIN_KEY'), os.environ.get('FKUCOIN_SECRET'), os.environ.get('FKUCOIN_PASS'))
    # print(trade.get_all_position())
    print(trade.create_market_order('XBTUSDTM', 'buy', '10', 1, '50000', '35000', 'primo'))

