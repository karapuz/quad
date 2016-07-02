'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

from   robbie.util.logging import logger
import robbie.echo.basestrat as basestrat
from   robbie.echo.stratutil import STRATSTATE

# if nextState ==  STRATSTATE.CLOSING:
#     pass
# elif nextState ==  STRATSTATE.OPENING:
#     pass
# elif nextState ==  STRATSTATE.EMPTY:
#     pass
# else:
#     raise ValueError('Uknown nextState=%s' % nextState)

class Strategy(basestrat.BaseStrat):

    def __init__(self, agent, policy):
        super(Strategy, self).__init__(agent=agent, policy=policy)
    ##
    ##
    ##
    # self._src2snk    = {}
    # self._snk2src    = {}
    # self._cx2snk        = {}
    # self._snk2cx        = {}
    # self._cx2src        = {}
    # self._src2cx        = {}
    def srcPreUpdate(self, action, data):
        orderId     = data[ 'orderId']
        # symbol      = data[ 'symbol' ]
        # qty         = data[ 'qty'    ]

        if action  == STRATSTATE.ORDERTYPE_NEW:
            # either open or close - REFLECT does not care
            echoAction, echoData = self.getEchoOrder( data )
            echoOrderId = echoData['orderId']

            self.linkSignalEchoOrders(signalOrderId=orderId, echoOrderId=echoOrderId)
            self.addActionData( {'action':echoAction, 'data':echoData} )

        elif action  == STRATSTATE.ORDERTYPE_CXRX:
            origOrderId = data['origOrderId' ]

            self.linkOrigOrderCx(orderId=orderId, origOrderId=origOrderId)
            echoOrderId = self._src2snk[ origOrderId ]

            echoAction, echoData = self.getEchoCancelOrder( origOrderId=echoOrderId, data=data )
            self.addActionData( {'action':echoAction, 'data':echoData} )

        elif action  == STRATSTATE.ORDERTYPE_FILL:
            pass

        else:
            msg = 'Uknown action=%s for data=%s' % (str(action), str(data))
            logger.error(msg)

    def snkPreUpdate(self, action, data):
        pass

    def snkPostUpdate(self, action, data):
        pass

    def srcPostUpdate(self, action, data):
        pass

    def newMsg(self):
        actionData = self._actionData
        self._actionData = []
        return actionData