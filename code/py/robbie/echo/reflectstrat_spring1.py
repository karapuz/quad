'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

import copy
import robbie.echo.order as echoorder
from   robbie.util.logging import logger
import robbie.echo.basestrat as basestrat
import robbie.echo.stratutil as stratutil
from   robbie.echo.stratutil import STRATSTATE


class Strategy(basestrat.BaseStrat):

    def __init__(self, agent, policy):
        super(Strategy, self).__init__(agent=agent, policy=policy, mode=stratutil.EXECUTION_MODE.NEW_FILL_CX)
    ##
    ##
    ##
    def srcPreUpdate(self, action, data):
        orderId     = data[ 'orderId']

        # NEW dictates what to do wtih SIGNAL. Signal is always against SRC
        if action  == STRATSTATE.ORDERTYPE_NEW:
            echoAction, echoData = self.getEchoOrder( data )
            echoOrderId = echoData['orderId']

            if self.isSrcOpenSignal( action=action, data=data ):
                self.snkAddOpenLegToOrder( echoData=echoData )
                self.addActionData( {'action':echoAction, 'data':echoData} )

            elif self.isSrcCloseSignal( action=action, data=data ):
                self.snkAddCloseLegToOrder( echoData=echoData )
                # self.addActionData( {'action':echoAction, 'data':echoData} )
            else:
                raise ValueError('Should be either Open or Close. What is this? %s' % str(data))

            self.linkSignalEchoOrders(signalOrderId=orderId, echoOrderId=echoOrderId)

        # FILL dictates what to do with ECHO trades. It is always against SNK
        elif action  == STRATSTATE.ORDERTYPE_FILL:
            symbol  = data[ 'symbol']
            if self.isSrcCloseSignal( action=action, data=data ):
                for order in self.getOrdersForSymbol(symbol):
                    self.addCancelOrder( delay=1, order=order )
                    if self.snkHasRealizedOpen(order):
                        self.addLiquidateOrder( delay=5, order=order )

        # CX dictates what to do with ECHO trades. It is always against SNK
        elif action  == STRATSTATE.ORDERTYPE_CXRX:
            origOrderId = data['origOrderId' ]

            self.linkOrigOrderCx(orderId=orderId, origOrderId=origOrderId)
            echoOrderId = self._src2snk[ origOrderId ]

            echoAction, echoData = self.getEchoCancelOrder( origOrderId=echoOrderId, data=data )
            self.addActionData( {'action':echoAction, 'data':echoData} )

        else:
            msg = 'Unknown action=%s for data=%s' % (str(action), str(data))
            logger.error(msg)

    def isSrcOpenSignal( self, action, data):
        ''' check if this can be qualified as an open order '''
        symbol  = data[ 'symbol' ]
        qty     = data[ 'qty'    ]
        rlzd    = self.getRealizedBySymbol(target='SRC', tag=symbol )
        return rlzd * qty >= 0

    def snkAddCloseLegToOrder( self, echoData ):
        ''' we are closing one of the open orders with a close '''
        action  = STRATSTATE.ORDERTYPE_NEW
        symbol  = echoData[ 'symbol' ]
        q       = self._orderQueueBySymbol
        if symbol not in q:
            logger.error('Should have symbol=%s', symbol)
            return

        qq = q[ symbol ]
        if not len( qq ):
            logger.error('Should have data for symbol=%s', symbol)
            return

        closeQty    = 0
        qty         = echoData[ 'qty' ]

        for ix in xrange( len(qq) ):
            if abs(closeQty) >= abs(qty):
                break

            order       = q[ symbol ][ix]
            if order.getCloseOrder():
                continue

            orderId             = stratutil.newOrderId('ECHO')
            openOrder           = order.getOpenOrder()
            closeOrder          = copy.deepcopy( echoData )
            closeOrder[ 'qty' ] = -1*openOrder[ 'qty' ]
            closeOrder[ 'orderId' ] = orderId
            order.addCloseOrder(closeOrder=closeOrder)

            logger.debug('closeQty(%d) for qty(%d) for symbol=%s', closeQty, qty, symbol)
            logger.debug('snkAddCloseLegToOrder: order=%s', str(order))
            self.addActionData( {'action':action, 'data':closeOrder} )

            closeQty += closeOrder[ 'qty' ]

        if closeQty < qty:
            logger.error('closeQty(%d) for qty(%d) for symbol=%s', closeQty, qty, symbol)
            return

    def snkAddOpenLegToOrder( self, echoData):
        ''' '''
        symbol  = echoData[ 'symbol' ]
        order   = echoorder.EchoOrder(openOrder=echoData)
        q       = self._orderQueueBySymbol
        if symbol not in q:
            q[ symbol ] = []
        q[ symbol ].append( order )
        logger.debug('add order=%s', str(order))

    def isSrcCloseSignal( self, action, data):
        ''' '''
        return not self.isSrcOpenSignal( action=action, data=data)

    def snkPreUpdate(self, action, data):
        pass

    def snkPostUpdate(self, action, data):
        pass

    def srcPostUpdate(self, action, data):
        pass

    # def isSnkOpenOrder( self, action, data ):
    #     ''' '''
    #     symbol  = data[ 'symbol' ]
    #     qty     = data[ 'qty'    ]
    #     rlzd    = self.getRealizedBySymbol(target='SNK', symbol=symbol )
    #     return rlzd * qty >= 0
    #
    # def isSnkCloseOrder( self, action, data):
    #     ''' '''
    #     return not self.isSnkOpenOrder( action=action, data=data )

    # def snkHasPendingOpen( self, action, data):
    #     ''' '''
    #     symbol  = data[ 'symbol' ]
    #     qty     = data[ 'qty'    ]
    #     if qty > 0:
    #         pnd     = self.getPendingBySymbol(target='SNK', symbol=symbol, side='short' )
    #         return True
    #     elif qty < 0:
    #         pnd     = self.getPendingBySymbol(target='SNK', symbol=symbol, side='long' )
    #         return True
    #     else:
    #         return False

    # def snkHasPendingClose( self, action, data):
    #     symbol  = data[ 'symbol' ]
    #     qty     = data[ 'qty'    ]
    #     pnd     = self.getPendingBySymbol(target='SNK', symbol=symbol )
    #     return pnd * qty < 0


    def snkHasRealizedOpen(self, order):
        openOrderId = order.getOpenOrder()[ 'orderId' ]
        openRlzd    = self.getRealizedByOrderId(target='SNK', tag=openOrderId, shouldExist=False)
        return openRlzd
