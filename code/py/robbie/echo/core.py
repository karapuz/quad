'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.core module
'''

import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import  robbie.util.symboldb as symboldb
import robbie.echo.orderstate as orderstate

'''
    def onSubmit( self, message, execType, orderStatus ):
        self._signalStrat.onNew( execTime=txTime, orderId=orderId, symbol=symbol, qty=cxqty )

    def onOrderFill( self, message, execType, orderStatus ):
        self._signalStrat.onFill( execTime=txTime, orderId=orderId, symbol=symbol, qty=qty, price=lastPx )

    def onOrderPendingCancel( self, message, execType, orderStatus ):
        self._signalStrat.onCxRx( execTime=txTime, orderId=orderId, symbol=symbol, qty=cxqty )

    def onOrderCancel( self, message, execType, orderStatus ):
        self._signalStrat.onCxRx( execTime=txTime, orderId=orderId, symbol=symbol, qty=cxqty )

    def onOrderReject( self, message, execType, orderStatus ):
        self._signalStrat.onCxRx( execTime=txTime, orderId=orderId, symbol=symbol, qty=cxqty )
'''

class SignalStrat(object):
    def __init__(self):
        self._symIds = symboldb.currentSymbols()
        self._maxNum = 1000000
        self._orderstate = orderstate.OrderState(
            readOnly    = False,
            maxNum      = self._maxNum,
            symIds      = self._symIds,
            debug       = True )

    def onNew(self, execTime, orderId, symbol, qty, price):
        '''
        1. we either start a new signal (current position is 0)
        2. we are extending current position (current position exists, and in the same direction)
        3. we are closing (current position exists and in the opposite direction)
        '''
        symIx = self._orderstate.getIxByTag(symbol)
        if self._orderstate.getStateByIx()

    def onFill(self, execTime, orderId, symbol, qty, price):
        pass

    def onCxRx(self, execTime, orderId, symbol, qty):
        pass
