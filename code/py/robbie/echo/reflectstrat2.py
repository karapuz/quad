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

    def __init__(self, agent, policy, mktprice):
        super(Strategy, self).__init__(agent=agent, policy=policy, mode=stratutil.EXECUTION_MODE.FILL_ONLY)
    ##
    ##
    ##
    def srcPreUpdate(self, action, data, mktPrice):
        orderId     = data[ 'orderId']

        if action  == STRATSTATE.ORDERTYPE_NEW:
            logger.error('Unexpected action=%s', action)

        elif action  == STRATSTATE.ORDERTYPE_CXRX:
            logger.error('Unexpected action=%s', action)

        elif action  == STRATSTATE.ORDERTYPE_FILL:
            # either open or close - REFLECT does not care
            echoAction, echoData = self.getEchoOrder( data )
            echoOrderId = echoData['orderId']

            self.linkSignalEchoOrders(signalOrderId=orderId, echoOrderId=echoOrderId)
            self.addActionData( {'action':echoAction, 'data':echoData} )

        else:
            msg = 'Unknown action=%s for data=%s' % (str(action), str(data))
            logger.error(msg)

    def snkPreUpdate(self, action, data):
        pass

    def snkPostUpdate(self, action, data):
        pass

    def srcPostUpdate(self, action, data, mktPrice):
        pass

