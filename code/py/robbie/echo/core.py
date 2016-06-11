'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.core module
'''

import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger

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
        self._strip = {
            'INSTRUMENT'    : [],
            'ORDER_NEW'     : [],
            'ORDER_FILLED'  : [],
            'ORDER_CXRX'    : [],
            'ORDER_CXRXED'  : [],
        }

    def onNew( self, execTime, orderId, symbol, qty ):
        pass

    def onFill( self, execTime, orderId, symbol, qty, price):
        pass

    def onCxRx( execTime, orderId, symbol, qty):
        pass
