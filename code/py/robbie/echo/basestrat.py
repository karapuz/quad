'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

import zmq
import json
from   threading import Timer
import robbie.tweak.value as twkval
import robbie.util.exposure as utexp
from   robbie.util.logging import logger
import robbie.echo.stratutil as stratutil
import robbie.util.filelogging as filelogging
from   robbie.echo.stratutil import STRATSTATE
import robbie.echo.echoorderstate as echoorderstate

def getOrderStateDomain(target, agent):
    if target == 'SRC':
        return '%s-src' % agent
    elif target == 'SNK':
        return '%s-snk' % agent
    else:
        raise ValueError('Uknown target=%s' % target)

def setSOD(agent, strat ):
    path = twkval.getenv('run_sodpath')
    if path is None:
        logger.debug('basestrat.setSOD: No SOD')
        return
    exposure = utexp.loadFromCsv(path=path)
    return utexp.uploadIntoStrip(
            agent    = agent,
            exposure = exposure,
            strat    = strat )

class BaseStrat(object):

    def __init__(self, agent, policy, mode):
        self._agent     = agent
        self._srcOrders = echoorderstate.EchoOrderState(
                                            getOrderStateDomain(target='SRC', agent=agent),
                                            mode=mode)
        self._snkOrders = echoorderstate.EchoOrderState(
                                            getOrderStateDomain(target='SNK', agent=agent),
                                            mode=mode)
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
        self._agent_orderCmd= None
        self._context       = None
        self._sender        = None

        name                = agent
        domain              = twkval.getenv('run_domain')
        user                = twkval.getenv('env_userName')
        session             = twkval.getenv('run_session')
        attrs               = ( 'signalName', 'orderType', 'orderId', 'origOrderId', 'symbol', 'qty', 'price', 'timeInForce', 'execTime', 'venue' )

        vars                = dict( domain=domain, user=user, session=session, name=name, attrs=attrs )
        self._logger        = filelogging.getFileLogger(**vars)

    def _onSnkNew(self, action, data):
        data = dict(
            execTime    = data['execTime'],
            orderId     = data['orderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
            price       = float(data['price'])
            )
        self._snkOrders.onNew( **data )
        self._logger.debug(label='onSnkNew', args=data)

    def _onSnkFill(self, action, data):
        data = dict(
            execTime    = data['execTime'],
            orderId     = data['orderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
            price       = float(data['price'])
        )
        self._logger.debug(label='onSnkFill', args=data)
        self._snkOrders.onFill( **data )

    def _onSnkCxRx(self, action, data):
        data = dict(
            execTime    = data['execTime'],
            orderId     = data['origOrderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
            )
        self._logger.debug(label='onSnkCxRx', args=data)
        self._snkOrders.onCxRx( **data )

    def _onSrcNew(self, action, data):
        data = dict(
            execTime    = data['execTime'],
            orderId     = data['orderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
            price       = float(data['price'])
        )
        self._logger.debug(label='onSrcNew', args=data)
        self._srcOrders.onNew( **data)

    def _onSrcFill(self, action, data):
        data = dict(
            execTime    = data['execTime'],
            orderId     = data['orderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
            price       = float(data['price'])
        )
        self._logger.debug(label='onSrcFill', args=data)
        self._srcOrders.onFill(**data)

    def _onSrcCxRx(self, action, data):
        data = dict(
            execTime    = data['execTime'],
            orderId     = data['origOrderId'],
            symbol      = data['symbol'],
            qty         = int(data['qty']),
        )
        self._logger.debug(label='onSrcCxRx', args=data)
        self._srcOrders.onCxRx( **data )
    ##
    ##
    ##
    def snkPreUpdate(self, action, data):
        pass

    def snkPostUpdate(self, action, data):
        pass

    def snkUpdate(self, action, data):
        self._snkAction2proc[action](action=action, data=data)

    def srcUpdate(self, action, data, mktPrice):
        self._srcAction2proc[action](action=action, data=data)

    def srcPreUpdate(self, action, data, mktPrice):
        pass

    def srcPostUpdate(self, action, data, mktPrice):
        pass

    def getTargetOrderState(self, target):
        if target == 'SNK':
            orderstat = self._snkOrders.getOrderState()
        elif target == 'SRC':
            orderstat = self._srcOrders.getOrderState()
        else:
            logger.error('Uknown target=%s', target)
        return orderstat

    def linkSignalEchoOrders(self, signalOrderId, echoOrderId):
        ''' '''
        self._snk2src[ echoOrderId   ] = signalOrderId
        self._src2snk[ signalOrderId ] = echoOrderId
        logger.debug('basestrat: new %s --> %s', signalOrderId, echoOrderId)

    def getEchoOrdersForSignal(self, signalOrderId):
        ''' '''
        return self._src2snk[ signalOrderId ]

    def linkOrigOrderCx(self, orderId, origOrderId):
        ''' '''
        self._src2cx[ origOrderId ] = orderId
        self._cx2src[ orderId     ] = origOrderId
        logger.debug('basestrat:  cx %s --> %s', orderId, origOrderId)

    def getOrigForOrderCx(self, orderId, origOrderId):
        ''' '''
        return self._cx2src[ orderId     ]

    def getCurrentPending( self, target, tag ):
        ''' '''
        orderState = self.getTargetOrderState(target=target)
        ix  = orderState.getIxByTag( tag )
        return orderState.getPendingByIx( ix=ix )

    getPendingByOrderId = getCurrentPending

    def getCurrentState( self, target, where='all', which='pending', how='pandas'):
        ''' '''
        orderState = self.getTargetOrderState(target=target)
        return orderState.getCurrentState(where=where, which=which, how=how)

    def getRealizedBySymbol(self, target, tag, shouldExist=True ):
        ''' '''
        orderState = self.getTargetOrderState(target=target)
        return orderState.getRealizedByTag(tag=tag, shouldExist=shouldExist )

    getRealizedByOrderId = getRealizedBySymbol

    def getPendingBySymbol(self, target, symbol, side=None ):
        ''' '''
        orderState = self.getTargetOrderState(target=target)
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

    #newMsg = getActionData

    def getActionOrders(self):
        ''' '''
        q = self._actionOrders
        self._actionOrders = []
        return q

    def getOrderCmdCon(self):
        if self._context is None:
            self._agent_orderCmd  = "ORDER_CMD"
            self._context         = zmq.Context.instance()
            self._sender          = self._context.socket(zmq.PAIR)
            self._sender.connect("inproc://%s" % self._agent_orderCmd)
        return self._sender

    def startOrdersToAction(self):
        byTime = {}
        for orderAction in self.getActionOrders():
            # dict(delay=delay, order=order, orderType='CANCEL')
            # dict(delay=delay, order=order, orderType='LIQUIDATE')
            delay = orderAction['delay']
            if delay not in byTime:
                byTime[ delay ] = []
            byTime[ delay ].append( orderAction )

        for delay, actions in byTime.iteritems():
            Timer(delay, self.transferOrders, (actions,)).start()

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
                    orderData = {
                        'orderType'     : 'CANCEL',
                        'orderId'       : stratutil.newOrderId('EO-CX'),
                        'origOrderId'   : openOrderId,
                        'venue'         : venue,
                        'symbol'        : symbol,
                        'qty'           : openPend,
                        'execTime'      : 'NOW',
                    }
                    data.append(orderData)
                    self._logger.debug(label='OPENPEND-%s' % orderType, args=orderData)

                if closeOrder:
                    closeOrderId    = closeOrder[ 'orderId' ]
                    closePend       = self.getPendingByOrderId(target='SNK', tag=closeOrderId)
                else:
                    closePend       = 0

                if closePend:
                    closeOrderId    = closeOrder[ 'orderId' ]
                    orderData = {
                        'orderType'     : 'CANCEL',
                        'orderId'       : stratutil.newOrderId('EC-CX'),
                        'origOrderId'   : closeOrderId,
                        'venue'         : venue,
                        'symbol'        : symbol,
                        'qty'           : openPend,
                        'execTime'      : 'NOW',
                    }
                    data.append( orderData )
                    self._logger.debug(label='CLOSEPEND-%s' % orderType, args=orderData)

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
                    orderData = {
                        'orderType'     : 'MARKET',
                        'orderId'       : stratutil.newOrderId('EOC-LQ'),
                        'origOrderId'   : openOrderId,
                        'venue'         : venue,
                        'symbol'        : symbol,
                        'qty'           : -(closeRlzd + openPend),
                        'execTime'      : 'NOW',
                    }
                    data.append( orderData )
                    self._logger.debug(label='REALIZED-%s' % orderType, args=orderData)

            if orderType not in ('LIQUIDATE', 'CANCEL'):
                raise ValueError('Unknown orderType=%s' % orderType)

        self.addActionData(data=data)

    def getOrdersForSymbol(self, symbol):
        q = self._orderQueueBySymbol
        if symbol not in q:
            q[ symbol ] = []
        qq = q[ symbol ]
        q[ symbol ] = []
        return qq

    def isSrcClosingOrder(self, action):
        pass