'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

import robbie.echo.core as echocore
from   robbie.util.logging import logger
import robbie.echo.stratutil as stratutil
from   robbie.echo.stratutil import STRATSTATE

'''
msgd = dict(action='new',  data=dict(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price))
msgd = dict(action='fill', data=dict(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price))
msgd = dict(action='cxrx', data=dict(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty))
'''
import copy

class StratPolicy(object):
    pass

class ScaleVenuePolicy(StratPolicy):
    def __init__(self, scale, venue):
        self._scale = scale
        self._venue = venue

    def newOrder(self, orderId, data):
        qty     = data[ 'qty'   ]
        venue   = data.get( 'venue' )
        d = copy.deepcopy(data)
        d[ 'orderId' ] = orderId
        d[ 'qty'     ] = int(self._scale * qty )
        d[ 'venue'   ] = self._venue
        return d

    def newCxOrder( self, orderId, origOrderId, origData ):
        qty     = origData[ 'qty'   ]
        venue   = origData.get( 'venue' )
        d = copy.deepcopy(origData)
        d[ 'orderId'     ] = orderId
        d[ 'origOrderId' ] = origOrderId
        d[ 'qty'         ] = qty
        d[ 'venue'       ] = self._venue
        return d

class BaseStrat(object):

    def __init__(self, agent, policy):
        self._agent     = agent
        self._srcOrders = echocore.EchoOrderState('%s-src' % agent)
        self._snkOrders = echocore.EchoOrderState('%s-snk' % agent)
        self._policy    = policy

        self._snkAction2proc = {
            STRATSTATE.ORDERTYPE_NEW    : self._onSnkNew,
            STRATSTATE.ORDERTYPE_FILL   : self._onSnkFill,
            STRATSTATE.ORDERTYPE_CXRX   : self._onSnkCxRx,
        }

        self._srcAction2proc = {
            STRATSTATE.ORDERTYPE_NEW    : self._onSrcNew,
            STRATSTATE.ORDERTYPE_FILL   : self._onSrcFill,
            STRATSTATE.ORDERTYPE_CXRX   : self._onSrcCxRx,
        }
    ##
    ##
    ##
        self._src2snk   = {}
        self._snk2src   = {}
        self._cx2snk    = {}
        self._snk2cx    = {}
        self._cx2src    = {}
        self._src2cx    = {}
        self._actionData= []

    def addActionData(self, data ):
        self._actionData.append( data )

    def getActionData(self):
        actionData = self._actionData
        self._actionData = []
        return actionData

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
            orderId     = data['origOrderId'],
            symbol      = data['symbol'],
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

    def _getTargetOrderState(self, target):
        if target == 'SNK':
            orderstat = self._snkOrders.getOrderState()
        elif target == 'SRC':
            orderstat = self._srcOrders.getOrderState()
        else:
            logger.error('Uknown target=%s', target)
        return orderstat

    def getEchoOrder( self, data ):
        orderId          = stratutil.newOrderId('ECHO')
        echoData    = self._policy.newOrder(
                            orderId = orderId,
                            data    = data )
        echoAction  = STRATSTATE.ORDERTYPE_NEW
        return echoAction, echoData

    def getEchoCancelOrder( self, origOrderId, data ):
        echoAction       = STRATSTATE.ORDERTYPE_CXRX

        echoQty          = self.getCurrentPending( target='SNK', orderId=origOrderId )
        orderId          = stratutil.newOrderId('ECHO')
        origData         = {
                            'origOriderId'  : origOrderId,
                            'orderId'       : orderId,
                            'venue'         : data.get('venue'),
                            'symbol'        : data['symbol'],
                            'qty'           : echoQty,
                            'execTime'      : 'NOW',
        }
        echoData    = self._policy.newCxOrder(
                            orderId     = orderId,
                            origOrderId = origOrderId,
                            origData    = origData)

        return echoAction, echoData

    def linkSignalEchoOrders(self, signalOrderId, echoOrderId):
        self._snk2src[ echoOrderId   ] = signalOrderId
        self._src2snk[ signalOrderId ] = echoOrderId
        logger.debug('basestrat: new %s --> %s', signalOrderId, echoOrderId)

    def linkOrigOrderCx(self, orderId, origOrderId):
        self._src2cx[ origOrderId ] = orderId
        self._cx2src[ orderId     ] = origOrderId
        logger.debug('basestrat:  cx %s --> %s', orderId, origOrderId)

    def getCurrentPending( self, target, orderId ):
        orderState = self._getTargetOrderState(target=target)
        ix  = orderState.getIxByTag( orderId )
        qty = orderState.getPendingByIx( ix=ix )
        return qty