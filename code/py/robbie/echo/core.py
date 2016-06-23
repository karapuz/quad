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
        self._maxNum    = symboldb._maxNum

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
        if self._orderstate.checkExistTag(orderId):
            self._orderstate.addError(status='DUPLICATE_NEW', data=(signalName, execTime, orderId, symbol, qty, price), msg='DUPLICATE_NEW')
            msg = 'Duplicate new for orderId=%s symbol=%s qty=%s' % (orderId, symbol, qty)
            logger.error(msg)
            return
        logger.debug('comm.send onNew:%s' % str(msgd))
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addPendingByIx(ix=ixs,vals=(qty,qty))

    def onFill(self, signalName, execTime, orderId, symbol, qty, price):
        comm = self._sig2comm[ signalName ]
        msgd = dict(action='fill', signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price)
        msg  = json.dumps(msgd)
        logger.debug('comm.send onFill:%s' % str(msgd))
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addRealizedByIx(ix=ixs,vals=(qty,qty))

    def onCxRx(self, signalName, execTime, orderId, symbol, qty):
        comm = self._sig2comm[ signalName ]
        msgd = dict(action='cxrx', signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty)
        msg  = json.dumps(msgd)
        logger.debug('comm.send onCxRx:%s' % str(msgd))
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

class EchoOrderState(object):
    def __init__(self, domain):
        '''
        book keep order status
        translate into

            a. open    signal
            b. close   signal
            c. cancel  signal

        '''

        self._symbols    = symboldb.currentSymbols()
        self._symIds     = symboldb.symbol2id(self._symbols)
        self._maxNum     = symboldb._maxNum

        with twkcx.Tweaks(run_domain=domain):
            self._orderstate = orderstate.OrderState(
                    readOnly    = False,
                    maxNum      = self._maxNum,
                    symIds      = self._symIds,
                    debug       = True )

    def onNew(self, execTime, orderId, symbol, qty, price):
        data = (execTime, orderId, symbol, qty, price)
        if self._orderstate.checkExistTag(orderId):
            self._orderstate.addError(status='DUPLICATE_NEW', data=data, msg='DUPLICATE_NEW')
            msg = 'Duplicate new for orderId=%s symbol=%s qty=%s' % (orderId, symbol, qty)
            logger.error(msg)
            return
        logger.debug('echo onNew:%s' % str(data))
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addPendingByIx(ix=ixs,vals=(qty,qty))

    def onFill(self, execTime, orderId, symbol, qty, price):
        data = execTime, orderId, symbol, qty, price
        logger.debug('echo onFill:%s' % str(data))
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addRealizedByIx(ix=ixs,vals=(qty,qty))

    def onCxRx(self, execTime, orderId, symbol, qty):
        data = (execTime, orderId, symbol, qty)
        logger.debug('echo onCxRx:%s' % str(data))
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addCanceledByIx(ix=ixs,vals=(qty,qty))
