'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.core module
'''

import json
import robbie.tweak.context as twkcx
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.echo.orderstate as orderstate
from   robbie.echo.stratutil import STRATSTATE

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

    def onNew(self, signalName, execTime, orderId, symbol, qty, price, orderType):
        if self._orderstate.checkExistTag(orderId):
            self._orderstate.addError(
                status = 'DUPLICATE_NEW',
                data  = (signalName, execTime, orderId, symbol, qty, price, orderType),
                msg   = 'DUPLICATE_NEW')

            msg = 'Duplicate new for orderId=%s symbol=%s qty=%s' % (orderId, symbol, qty)
            logger.error(msg)
            return

        comm    = self._sig2comm[ signalName ]
        action  = STRATSTATE.ORDERTYPE_NEW
        msgd    = dict(
                    action = action,
                    data   = dict(
                                    signalName  = signalName,
                                    execTime    = execTime,
                                    orderId     = orderId,
                                    symbol      = symbol,
                                    qty         = qty,
                                    price       = price,
                                    orderType   = orderType))
        msg  = json.dumps(msgd)
        logger.debug('comm.send onNew:%s' % str(msgd))
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addPendingByIx(ix=ixs,vals=(qty,qty))

    def onFill(self, signalName, execTime, orderId, symbol, qty, price):
        comm    = self._sig2comm[ signalName ]
        action  = STRATSTATE.ORDERTYPE_FILL
        msgd    = dict(action=action , data=dict(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price))
        msg     = json.dumps(msgd)
        logger.debug('comm.send onFill:%s' % str(msgd))
        comm.send( msg )
        ixs     = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addRealizedByIx(ix=ixs,vals=(qty,qty))

    def onCxRx(self, signalName, execTime, orderId, symbol, qty, origOrderId):
        comm    = self._sig2comm[ signalName ]
        action  = STRATSTATE.ORDERTYPE_NEW
        msgd    = dict(action=action, data=dict(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, origOrderId=origOrderId))
        msg     = json.dumps(msgd)
        logger.debug('comm.send onCxRx:%s' % str(msgd))
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addCanceledByIx(ix=ixs,vals=(qty,qty))

    def getOrderState(self):
        return self._orderstate

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
        self._maxNum     = symboldb._maxNum

        with twkcx.Tweaks(run_domain=domain):
            self._orderstate = orderstate.OrderState(
                    readOnly    = False,
                    maxNum      = self._maxNum,
                    symbols     = self._symbols,
                    debug       = True )

    def onNew(self, execTime, orderId, symbol, qty, price):
        data = (execTime, orderId, symbol, qty, price)
        if self._orderstate.checkExistTag(orderId):
            self._orderstate.addError(status='DUPLICATE_NEW', data=data, msg='DUPLICATE_NEW')
            msg = 'Duplicate new for orderId=%s symbol=%s qty=%s' % (orderId, symbol, qty)
            logger.error(msg)
            return
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addPendingByIx(ix=ixs,vals=(qty,qty))
        logger.debug('coreecho: onNew:%s ixs=%s', str(data), ixs)

    def onFill(self, execTime, orderId, symbol, qty, price):
        data = execTime, orderId, symbol, qty, price
        logger.debug('coreecho: onFill:%s' % str(data))
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addRealizedByIx(ix=ixs,vals=(qty,qty))

    def onCxRx(self, execTime, orderId, symbol, qty):
        data = (execTime, orderId, symbol, qty)
        logger.debug('coreecho: onCxRx:%s' % str(data))
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addCanceledByIx(ix=ixs,vals=(qty,qty))

    def getOrderState(self):
        return self._orderstate
