'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

import robbie.echo.core as echocore
from   robbie.util.logging import logger
import robbie.echo.stratutil as stratutil

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
    def snkPreUpdate(self, action, data):
        pass

    def snkPostUpdate(self, action, data):
        pass

    def snkUpdate(self, action, data):
        self._snkAction2proc[action](action=action, data=data)

    def srcUpdate(self, action, data):
        self._srcAction2proc[action](action=action, data=data)

    def srcPreUpdate(self, action, data):
        pass

    def srcPostUpdate(self, action, data):
        pass

    def newMsg(self):
        status, msg = None, None
        return status, msg

    def _getTargetOrderState(self, target):
        if target == 'SNK':
            orderstat = self._srcOrders
        elif target == 'SRC':
            orderstat = self._snkOrders
        else:
            logger.error('Uknown target=%s', target)
        return orderstat

    def _hasPositionForSymbol(self, target, symbol):
        orderstat   = self._getTargetOrderState(target=target)

        ix          = orderstat.getIxByTag(tag=symbol)
        pendingPos  = orderstat.getPendingByIx( ix )
        realizedPos = orderstat.getRealizedByIx( ix )

        if pendingPos or realizedPos:
            return True
        else:
            return False

    def _getCurrentState(self, target, symbol):
        '''
            state
            CLOSING = 'CLOSING STATE'
            OPENING = 'OPENING STATE'
            EMPTY   = 'EMPTY STATE'
        '''
        orderstat   = self._getTargetOrderState(target=target)

        ix          = orderstat.getIxByTag(tag=symbol)
        pendingPos  = orderstat.getPendingByIx( ix )
        realizedPos = orderstat.getRealizedByIx( ix )

        state, sign = stratutil.getCurrentState(pendingPos=pendingPos, realizedPos=realizedPos)

        return state, sign

    def _getAction(self, target, qty, symbol):
        '''
            action
            ISSUEOPENORDER  = 'ISSUE OPEN ORDER'
            ISSUECLOSEORDER = 'ISSUE CLOSE ORDER'
        '''

        state, sign             = self._getCurrentState(target=target, symbol=symbol)
        nextState, nextAction   = stratutil.getAction( state=state, sign=sign, qty=qty)

        return nextState, nextAction

    def getEchoOpenOrder( self, data ):
        echoAction, echoData = None, None
        return echoAction, echoData

    def getEchoCancelOrder( self, data ):
        echoAction, echoData = None, None
        return echoAction, echoData

    def getEchoCloseOrder( self, data ):
        echoAction, echoData = None, None
        return echoAction, echoData
