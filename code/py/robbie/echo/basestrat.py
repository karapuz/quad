'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

import zmq
import json
from   threading import Timer
import robbie.echo.core as echocore
from   robbie.util.logging import logger
import robbie.echo.stratutil as stratutil
from   robbie.echo.stratutil import STRATSTATE

class BaseStrat(object):

    def __init__(self, agent, policy, mode):
        self._agent     = agent
        self._srcOrders = echocore.EchoOrderState('%s-src' % agent, mode=mode)
        self._snkOrders = echocore.EchoOrderState('%s-snk' % agent, mode=mode)
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
        self._src2snk       = {}
        self._snk2src       = {}
        self._cx2snk        = {}
        self._snk2cx        = {}
        self._cx2src        = {}
        self._src2cx        = {}
        self._actionData    = []
        self._actionOrders  = []
        self._orderQueueBySymbol = {}

        #
        # order cmd
        #
        self._agent_orderCmd  = None
        self._context         = None
        self._sender          = None

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
            orderId     = data['origOrderId'],
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
        echoAction  = STRATSTATE.ORDERTYPE_NEW
        orderId     = stratutil.newOrderId('ECHO')
        echoData    = self._policy.newOrder(
                            orderId = orderId,
                            data    = data )
        return echoAction, echoData

    def getEchoCancelOrder( self, origOrderId, data ):
        echoAction       = STRATSTATE.ORDERTYPE_CXRX

        echoQty          = self.getCurrentPending( target='SNK', orderId=origOrderId )
        orderId          = stratutil.newOrderId('ECHO')
        origData         = {
                            'origOrderId'   : origOrderId,
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
        ''' '''
        self._snk2src[ echoOrderId   ] = signalOrderId
        self._src2snk[ signalOrderId ] = echoOrderId
        logger.debug('basestrat: new %s --> %s', signalOrderId, echoOrderId)

    def linkOrigOrderCx(self, orderId, origOrderId):
        ''' '''
        self._src2cx[ origOrderId ] = orderId
        self._cx2src[ orderId     ] = origOrderId
        logger.debug('basestrat:  cx %s --> %s', orderId, origOrderId)

    def getCurrentPending( self, target, tag ):
        ''' '''
        orderState = self._getTargetOrderState(target=target)
        ix  = orderState.getIxByTag( tag )
        return orderState.getPendingByIx( ix=ix )

    getPendingByOrderId = getCurrentPending

    def getCurrentState( self, target, where='all', which='pending', how='pandas'):
        ''' '''
        orderState = self._getTargetOrderState(target=target)
        return orderState.getCurrentState(where=where, which=which, how=how)

    def getRealizedBySymbol(self, target, tag, shouldExist=True ):
        ''' '''
        orderState = self._getTargetOrderState(target=target)
        return orderState.getRealizedByTag(tag=tag, shouldExist=shouldExist )

    getRealizedByOrderId = getRealizedBySymbol

    def getPendingBySymbol(self, target, symbol, side=None ):
        ''' '''
        orderState = self._getTargetOrderState(target=target)
        l = orderState.getLongPendingByIx(tag=symbol )
        s = orderState.getShortPendingByIx(tag=symbol )

        if side == None:
            if l and not s:
                return l
            if s and not l:
                return s
            if s and l:
                logger.error('Confusing Pending state: both l=%s and s=%s', l, s)
                return l + s
        elif side == 'long':
            return l
        elif side == 'short':
            return s
        else:
            raise ValueError('Wrong side=%s' % side )

    def addActionData(self, data ):
        ''' '''
        if isinstance(data, (list, tuple)):
            self._actionData.extend( data )
        else:
            self._actionData.append( data )

    def addOrder( self, action ):
        self._actionOrders.append( action )

    def addCancelOrder( self, delay, order ):
        self.addOrder( dict(delay=delay, order=order, orderType='CANCEL') )

    def addLiquidateOrder( self, delay, order ):
        self.addOrder( dict(delay=delay, order=order, orderType='LIQUIDATE') )

    def getActionData(self):
        ''' '''
        q = self._actionData
        self._actionData = []
        return q

    newMsg = getActionData

    def getActionOrders(self):
        ''' '''
        q = self._actionOrders
        self._actionOrders = []
        return q

    def startOrdersToAction(self):
        byTime = {}
        for orderAction in self._actionOrders:
            # dict(delay=delay, order=order, orderType='CANCEL')
            # dict(delay=delay, order=order, orderType='LIQUIDATE')
            delay = orderAction['delay']
            if delay not in byTime:
                byTime[ delay ] = []
            byTime[ delay ].append( orderAction )

        for delay, actions in byTime.iteritems():
            Timer(delay, self.transferOrders, (actions,)).start()

    def getOrderCmdCon(self):
        if self._context is None:
            self._agent_orderCmd  = "ORDER_CMD"
            self._context         = zmq.Context.instance()
            self._sender          = self._context.socket(zmq.PAIR)
            self._sender.connect("inproc://%s" % self._agent_orderCmd)
        return self._sender

    def transferOrders(self, actions):
        sender          = self.getOrderCmdCon()
        msg             = json.dumps(actions)
        logger.debug('transferOrders-> %s', str(actions))
        sender.send(msg)

    def orderUpdate(self, actionOrder):
        # dict(delay=delay, order=order, orderType='CANCEL')
        # dict(delay=delay, order=order, orderType='LIQUIDATE')
        data = []
        for actionOrder in actionOrder:
            orderType       = actionOrder['orderType']

            order           = actionOrder['order']

            openOrder       = order.getOpenOrder()
            closeOrder      = order.getCloseOrder()

            symbol          = openOrder['symbol']
            openOrderId     = openOrder[ 'orderId' ]

            # for either liquidate or cancel, we need to cancel pendings
            if orderType in ('LIQUIDATE', 'CANCEL'):
                # cancel all pending orders

                openPend        = self.getPendingByOrderId(target='SNK', tag=openOrderId)
                venue           = 'NYSE'
                if openPend:
                    data.append({
                        'orderType'     : 'CANCEL',
                        'orderId'       : stratutil.newOrderId('EO-CX'),
                        'origOrderId'   : openOrderId,
                        'venue'         : venue,
                        'symbol'        : symbol,
                        'qty'           : openPend,
                        'execTime'      : 'NOW',
                    } )
                if closeOrder:
                    closeOrderId    = closeOrder[ 'orderId' ]
                    closePend       = self.getPendingByOrderId(target='SNK', tag=closeOrderId)
                else:
                    closePend       = 0

                if closePend:
                    closeOrderId    = closeOrder[ 'orderId' ]
                    data.append({
                        'orderType'     : 'CANCEL',
                        'orderId'       : stratutil.newOrderId('EC-CX'),
                        'origOrderId'   : closeOrderId,
                        'venue'         : venue,
                        'symbol'        : symbol,
                        'qty'           : openPend,
                        'execTime'      : 'NOW',
                    } )

            if orderType == 'LIQUIDATE':
                # liquidate all realized exposure

                openOrderId     = openOrder[ 'orderId' ]
                openRlzd        = self.getRealizedByOrderId(target='SNK', tag=openOrderId)
                if closeOrder:
                    closeOrderId    = closeOrder[ 'orderId' ]
                    closeRlzd       = self.getRealizedByOrderId(target='SNK', tag=closeOrderId)
                else:
                    closeRlzd       = 0

                venue           = 'NYSE'
                if openRlzd + closeRlzd:
                    data.append({
                        'orderType'     : 'MARKET',
                        'orderId'       : stratutil.newOrderId('EOC-LQ'),
                        'origOrderId'   : openOrderId,
                        'venue'         : venue,
                        'symbol'        : symbol,
                        'qty'           : -(closeRlzd + openPend),
                        'execTime'      : 'NOW',
                    } )

            if orderType not in ('LIQUIDATE', 'CANCEL'):
                raise ValueError('Unknown orderType=%s' % orderType)

        self.addActionData(data=data)

    def getOrdersForSymbol(self, symbol):
        q = self._orderQueueBySymbol
        if symbol not in q:
            q[ symbol ] = []
        return q[ symbol ]

    def isSrcClosingOrder(self, action):
        pass