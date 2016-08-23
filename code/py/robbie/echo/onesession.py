'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

import copy
import robbie.fix.util as fut
import robbie.echo.order as echoorder
from   robbie.util.logging import logger
import robbie.echo.basestrat as basestrat
import robbie.echo.stratutil as stratutil
from   robbie.echo.stratutil import STRATSTATE

'''
mktPrice: {
            symbol:
                {
                    'TRADE': trade,
                    'BID': bid,
                    'ASK': ask
                }
            }

'''
class Strategy(basestrat.BaseStrat):

    def __init__(self, agent, policy):
        super(Strategy, self).__init__(agent=agent, policy=policy, mode=stratutil.EXECUTION_MODE.NEW_FILL_CX)
    ##
    ##
    ##
    def getEchoOrder( self, data, mktPrice ):
        symbol      = data['symbol']
        orderType   = data['orderType']
        timeInForce = data['timeInForce']

        if orderType == fut.Val_OrdType_Market:
            if timeInForce == fut.Val_TimeInForce_OPG:
                # market on open - no change
                pass
            else:
                orderType = fut.Val_OrdType_Limit
                # move to Limit
                data['price']       = mktPrice[symbol]['TRADE']

        data['orderType']       = orderType
        data['timeInForce']     = timeInForce

        echoAction  = STRATSTATE.ORDERTYPE_NEW
        orderId     = stratutil.newOrderId('ECHO')
        echoData    = self._policy.newOrder(
                            orderId = orderId,
                            data    = data )
        return echoAction, echoData

    def getEchoCancelOrder( self, origOrderId, data ):
        echoAction       = STRATSTATE.ORDERTYPE_CXRX

        echoQty          = self.getCurrentPending( target='SNK', tag=origOrderId )
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

    def srcPreUpdate(self, action, data, mktPrice ):
        orderId     = data[ 'orderId']

        # NEW dictates what to do wtih SIGNAL. Signal is always against SRC
        if action  == STRATSTATE.ORDERTYPE_NEW:
            echoAction, echoData = self.getEchoOrder( data=data, mktPrice=mktPrice )
            echoOrderId = echoData['orderId']

            self.snkAddLegToOrder( echoData=echoData )
            self.addActionData( {'action':echoAction, 'data':echoData} )
            self.linkSignalEchoOrders(signalOrderId=orderId, echoOrderId=echoOrderId)

        # we ignore FILL under "one-session"
        elif action  == STRATSTATE.ORDERTYPE_FILL:
            pass

        # CX dictates what to do with ECHO trades. It is always against SNK
        elif action  == STRATSTATE.ORDERTYPE_CXRX:
            origOrderId = data[ 'origOrderId']
            echoOrigOrderId = self.getEchoOrdersForSignal(signalOrderId=origOrderId)
            echoAction, echoData = self.getEchoCancelOrder( origOrderId=echoOrigOrderId, data=data )
            self.addActionData( {'action':echoAction, 'data':echoData} )

        else:
            msg = 'Unknown action=%s for data=%s' % (str(action), str(data))
            logger.error(msg)

    def snkAddLegToOrder( self, echoData):
        ''' '''
        symbol  = echoData[ 'symbol' ]
        order   = echoorder.EchoOrder(openOrder=echoData)
        q       = self._orderQueueBySymbol
        if symbol not in q:
            q[ symbol ] = []
        q[ symbol ].append( order )
        logger.debug('add order=%s', str(order))

    def snkPreUpdate(self, action, data):
        pass

    def snkPostUpdate(self, action, data):
        pass

    def srcPostUpdate(self, action, data, mktPrice):
        pass

    def snkHasRealizedOpen(self, order):
        openOrderId = order.getOpenOrder()[ 'orderId' ]
        openRlzd    = self.getRealizedByOrderId(target='SNK', tag=openOrderId, shouldExist=False)
        return openRlzd

    def getLivePendingOrderBySymbol( self, target, symbol):
        return self.getOrderBySymbol( expType='pending', target='SNK', symbol=symbol)

    def getRealizedOrderBySymbol( self, target, symbol):
        return self.getOrderBySymbol( expType='realized', target='SNK', symbol=symbol)

    def getOrderBySymbol( self, expType, target, symbol):
        '''  {'ORDER3': 100.0} '''
        orderState = self._getTargetOrderState(target=target)
        symQty = orderState.getOrderBySymbol(expType=expType, symbol=symbol)
        return symQty

    def bbOrderUpdate(self, cmds):
        # dict(delay=delay, order=order, orderType='CANCEL')
        # dict(delay=delay, order=order, orderType='LIQUIDATE')
        timeInForce =  fut.Val_TimeInForce_DAY
        data        = []
        for cmd in cmds:
            action      = cmd['action']
            symbol      = cmd['symbol']
            signalName  = cmd['signalName']

            shortAction = 'CANCEL' if action == STRATSTATE.ORDERTYPE_SYMBOL_CANCEL else 'LIQUIDATE'

            if action in ( STRATSTATE.ORDERTYPE_SYMBOL_CANCEL, STRATSTATE.ORDERTYPE_SYMBOL_LIQUIDATE):
                # cancel all pending orders
                ordQty = self.getLivePendingOrderBySymbol( target='SNK', symbol=symbol)

                for origOrderId, qty in ordQty.iteritems():
                    d = {
                        'action'        : STRATSTATE.ORDERTYPE_CXRX,
                        'data'          : {
                                'action'        : STRATSTATE.ORDERTYPE_CXRX,
                                'orderId'       : stratutil.newOrderId('EO-CX'),
                                'origOrderId'   : origOrderId,
                                'symbol'        : symbol,
                                'qty'           : qty,
                                'signalName'    : signalName,
                                'timeInForce'   : timeInForce,
                            },
                        }
                    data.append(d)
                    self._logger.debug(label='PEND-%s' % shortAction, args=d)

            if action == STRATSTATE.ORDERTYPE_SYMBOL_LIQUIDATE:
                # liquidate all realized exposure
                rlzdOrdQty = self.getRealizedOrderBySymbol( target='SNK', symbol=symbol)
                for origOrderId, qty in rlzdOrdQty.iteritems():
                    d = {
                        'action'    : STRATSTATE.ORDERTYPE_NEW,
                        'data'      : {
                                'action'        : STRATSTATE.ORDERTYPE_NEW,
                                'orderType'     : fut.Val_OrdType_Market,
                                'orderId'       : stratutil.newOrderId('EOC-LQ'),
                                'origOrderId'   : origOrderId,
                                'symbol'        : symbol,
                                'qty'           : -qty,
                                'timeInForce'   : timeInForce,
                            },
                        }
                    data.append( d )
                    self._logger.debug(label='REALIZED-%s' % shortAction, args=d)

            if action not in ( STRATSTATE.ORDERTYPE_SYMBOL_CANCEL, STRATSTATE.ORDERTYPE_SYMBOL_LIQUIDATE):
                raise ValueError('Unknown orderType=%s' % action)

        return data
