'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.core module
'''

import json
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
    '''
    propagate signal to the appropriate agent almost as-is
    The conversion:
        onNew       -> 'new'
        onCancel    -> 'cx'
        onReject    -> 'rx'
        onFill      -> 'fill'
    '''
    def __init__(self, sig2comm):
        self._symbols   = symboldb.currentSymbols()
        self._symIds    = symboldb.symbol2id(self._symbols)
        self._maxNum    = 1000000

        self._orderstate = orderstate.OrderState(
                readOnly    = False,
                maxNum      = self._maxNum,
                symIds      = self._symIds,
                debug       = True )
        self._sig2comm  = sig2comm

    def onNew(self, signalName, execTime, orderId, symbol, qty, price):
        comm = self._sig2comm[ signalName ]
        msgd = dict(action='new', signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price)
        msg  = json.dumps(msgd)
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addPendingByIx(ix=ixs,vals=(qty,qty))

    def onFill(self, signalName, execTime, orderId, symbol, qty, price):
        comm = self._sig2comm[ signalName ]
        msgd = dict(action='fill', signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price)
        msg  = json.dumps(msgd)
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addRealizedByIx(ix=ixs,vals=(qty,qty))

    def onCxRx(self, signalName, execTime, orderId, symbol, qty):
        comm = self._sig2comm[ signalName ]
        msgd = dict(action='cxrx', signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty)
        msg  = json.dumps(msgd)
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addCanceledByIx(ix=ixs,vals=(qty,qty))

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

class EchoStrat(object):
    '''
    React to both signal
        formulate order
    React to execution
        formulate order
    '''
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
        1. Strategy has Open, Close and/or a Cancel Signal
        2. Strategy has the following life-cycle
            a. Open (triggered by New) order
                i) no positions for the symbol, or positions in the same direction
            b. Close (triggered by New) order
                i) there is a position for the symbol
            c. Cancel (triggered Cancel, or Reject) order
                i) there is position for the symbol

        '''
        symIx = self._orderstate.getIxByTag(symbol)
        #if self._orderstate.getStateByIx()

    def onFill(self, execTime, orderId, symbol, qty, price):
        pass

    def onCxRx(self, execTime, orderId, symbol, qty):
        pass
