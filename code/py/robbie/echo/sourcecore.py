'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.core module
'''

import json
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.echo.orderstate as orderstate
from   robbie.echo.stratutil import STRATSTATE, EXECUTION_MODE

class SourceStrat(object):
    '''
    propagate signal to the appropriate agent almost as-is
    The conversion:
        onNew       -> 'new'
        onCancel    -> 'cx'
        onReject    -> 'rx'
        onFill      -> 'fill'
    '''
    def __init__(self, sig2comm, mode):
        self._symbols   = symboldb.currentSymbols()
        self._symIds    = symboldb.symbol2id(self._symbols)
        self._maxNum    = symboldb._maxNum

        if mode == EXECUTION_MODE.NEW_FILL_CX:
            seePending = True
        elif mode == EXECUTION_MODE.FILL_ONLY:
            seePending = False
        else:
            raise ValueError('Unknown mode=%s' % mode)

        self._orderstate = orderstate.OrderState(
                readOnly    = False,
                maxNum      = self._maxNum,
                symbols     = self._symbols,
                seePending  = seePending,
                debug       = True )

        self._sig2comm  = sig2comm

    def onNew(self, signalName, execTime, orderId, symbol, orderType, timeInForce, qty, price, mktPrice):
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
                                    orderType   = orderType,
                                    timeInForce = timeInForce),
                    mktPrice = mktPrice,
                    )
        msg  = json.dumps(msgd)
        logger.debug('comm.send onNew:%s' % str(msgd))
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addPendingByIx(ix=ixs,vals=(qty,qty))

    def onFill(self, signalName, execTime, orderId, symbol, qty, price, mktPrice):
        comm    = self._sig2comm[ signalName ]
        action  = STRATSTATE.ORDERTYPE_FILL
        msgd    = dict(
                    action  = action ,
                    data    = dict(
                                    signalName  = signalName,
                                    execTime    = execTime,
                                    orderId     = orderId,
                                    symbol      = symbol,
                                    qty         = qty,
                                    price       = price),
                    mktPrice = mktPrice,
                    )
        msg     = json.dumps(msgd)
        logger.debug('comm.send onFill:%s' % str(msgd))
        comm.send( msg )
        ixs     = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addRealizedByIx(ix=ixs,vals=(qty,qty))

    def onCxRx(self, signalName, execTime, orderId, symbol, qty, origOrderId, mktPrice):
        comm    = self._sig2comm[ signalName ]
        action  = STRATSTATE.ORDERTYPE_CXRX
        msgd    = dict(
                    action  = action,
                    data    = dict(
                                    signalName  = signalName,
                                    execTime    = execTime,
                                    orderId     = orderId,
                                    symbol      = symbol,
                                    qty         = qty,
                                    origOrderId = origOrderId),
                    mktPrice = mktPrice,
                    )
        msg     = json.dumps(msgd)
        logger.debug('comm.send onCxRx:%s' % str(msgd))
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, origOrderId))
        self._orderstate.addCanceledByIx(ix=ixs,vals=(qty,qty))

    def getOrderState(self):
        return self._orderstate
