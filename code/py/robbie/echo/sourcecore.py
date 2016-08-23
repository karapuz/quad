'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.core module
'''

import json
import robbie.tweak.value as twkval
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.echo.orderstate as orderstate
import robbie.util.filelogging as filelogging
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

        domain      = twkval.getenv('run_domain')
        user        = twkval.getenv('env_userName')
        session     = twkval.getenv('run_session')
        attrs       = ( 'signalName', 'orderType', 'timeInForce', 'orderId', 'symbol', 'price', 'execTime', 'qty')
        vars        = dict( domain=domain, user=user, session=session, name='SOURCESTRAT', attrs=attrs )
        self._logger  = filelogging.getFileLogger(**vars)

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
        orderData   = dict(
                        signalName  = signalName,
                        execTime    = execTime,
                        orderId     = orderId,
                        symbol      = symbol,
                        qty         = qty,
                        price       = price,
                        orderType   = orderType,
                        timeInForce = timeInForce)
        msgd    = dict(
                    action  = action,
                    data    = orderData,
                    mktPrice = mktPrice,
                    )
        msg  = json.dumps(msgd)
        logger.debug('comm.send onNew:%s' % str(msgd))
        self._logger.debug(label='onNew', args=orderData)
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addPendingByIx(ix=ixs,vals=(qty,qty))

    def onFill(self, signalName, execTime, orderId, symbol, qty, price, mktPrice):
        comm    = self._sig2comm[ signalName ]
        action  = STRATSTATE.ORDERTYPE_FILL
        orderData = dict(
                        signalName  = signalName,
                        execTime    = execTime,
                        orderId     = orderId,
                        symbol      = symbol,
                        qty         = qty,
                        price       = price)
        msgd    = dict(
                    action  = action ,
                    data    = orderData,
                    mktPrice = mktPrice,
                    )
        msg     = json.dumps(msgd)
        logger.debug('comm.send onFill:%s' % str(msgd))
        self._logger.debug(label='onFill', args=orderData)
        comm.send( msg )
        ixs     = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addRealizedByIx(ix=ixs,vals=(qty,qty))

    def onCxRx(self, signalName, execTime, orderId, symbol, qty, origOrderId, mktPrice):
        comm    = self._sig2comm[ signalName ]
        action  = STRATSTATE.ORDERTYPE_CXRX
        orderData = dict(
                        signalName  = signalName,
                        execTime    = execTime,
                        orderId     = orderId,
                        symbol      = symbol,
                        qty         = qty,
                        origOrderId = origOrderId)
        msgd    = dict(
                    action  = action,
                    data    = orderData,
                    mktPrice = mktPrice,
                    )
        msg     = json.dumps(msgd)
        logger.debug('comm.send onCxRx:%s' % str(msgd))
        self._logger.debug(label='onCxRx', args=orderData)
        comm.send( msg )
        ixs = self._orderstate.addTags((symbol, origOrderId))
        self._orderstate.addCanceledByIx(ix=ixs,vals=(qty,qty))

    def getOrderState(self):
        return self._orderstate
