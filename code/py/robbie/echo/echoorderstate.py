'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.core module
'''

import json
import robbie.turf.util as turfutil
import robbie.tweak.context as twkcx
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.echo.orderstate as orderstate
from   robbie.echo.stratutil import STRATSTATE, EXECUTION_MODE

class EchoOrderState(object):
    def __init__(self, domain, mode):
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
            if mode == EXECUTION_MODE.NEW_FILL_CX:
                seePending = True
            elif mode == EXECUTION_MODE.FILL_ONLY:
                seePending = False
            else:
                raise ValueError('Unknown signalMode=%s' % mode)

            self._orderstate = orderstate.OrderState(
                    readOnly    = False,
                    maxNum      = self._maxNum,
                    symbols     = self._symbols,
                    seePending  = seePending,
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
