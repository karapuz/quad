'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

import robbie.echo.core as echocore

'''
msgd = dict(action='new',  data=dict(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price))
msgd = dict(action='fill', data=dict(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price))
msgd = dict(action='cxrx', data=dict(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty))
'''

class BaseStrat(object):

    def __init__(self, agent):
        self._agent     = agent
        self._srcOrders = echocore.EchoOrderState('%s-src' % agent)
        self._snkOrders = echocore.EchoOrderState('%s-snk' % agent)

        self._snkAction2proc = {
            'new' : self._onSnkNew,
            'fill' : self._onSnkFill,
            'cxrx' : self._onSnkCxRx,
        }

        self._srcAction2proc = {
            'new' : self._onSrcNew,
            'fill' : self._onSrcFill,
            'cxrx' : self._onSrcCxRx,
        }

    ##
    ##
    ##

    def _onSnkNew(self, action, data):
        self._snkOrders.onNew(
            execTime    = data['execTime'],
            orderId     = data['orderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
            price       = float(data['price'])
        )

    def _onSnkFill(self, action, data):
        self._snkOrders.onFill(
            execTime    = data['execTime'],
            orderId     = data['orderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
            price       = float(data['price'])
        )

    def _onSnkCxRx(self, action, data):
        self._snkOrders.onCxRx(
            execTime    = data['execTime'],
            orderId     = data['orderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
        )

    def _onSrcNew(self, action, data):
        self._srcOrders.onNew(
            execTime    = data['execTime'],
            orderId     = data['orderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
            price       = float(data['price'])
        )

    def _onSrcFill(self, action, data):
        self._srcOrders.onFill(
            execTime    = data['execTime'],
            orderId     = data['orderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
            price       = float(data['price'])
        )

    def _onSrcCxRx(self, action, data):
        self._srcOrders.onCxRx(
            execTime    = data['execTime'],
            orderId     = data['execTime'],
            symbol      = data['execTime'],
            qty         = int(data['qty']),
        )

    ##
    ##
    ##

    def processSrcMsg(self, action, data):
        self._srcAction2proc[action](action=action, data=data)

    def processSnkMsg(self, action, data):
        self._snkAction2proc[action](action=action, data=data)





