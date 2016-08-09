'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

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
    def srcPreUpdate(self, action, data, mktPrice):
        orderId     = data[ 'orderId']

        if action  == STRATSTATE.ORDERTYPE_NEW:
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
            msg = 'Unknown action=%s for data=%s' % (str(action), str(data))
            logger.error(msg)

    def snkPreUpdate(self, action, data):
        pass

    def snkPostUpdate(self, action, data):
        pass

    def srcPostUpdate(self, action, data, mktPrice):
        pass

