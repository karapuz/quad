'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

from   robbie.util.logging import logger
import robbie.echo.basestrat as basestrat
from   robbie.echo.stratutil import STRATSTATE

class Strategy(basestrat.BaseStrat):

    def __init__(self, agent):
        super(Strategy, self).__init__(agent)
    ##
    ##
    ##
    def snkPreUpdate(self, action, data):
        symbol  = data['symbol' ]
        qty     = data['qty'    ]
        nextState, nextAction = self._getAction(target='SNK', qty=qty, symbol=symbol)

        if nextState ==  STRATSTATE.CLOSING:
            pass
        elif nextState ==  STRATSTATE.OPENING:
            pass
        elif nextState ==  STRATSTATE.EMPTY:
            pass
        else:
            raise ValueError('Uknown nextState=%s' % nextState)

        actionData = []
        if nextAction ==  STRATSTATE.ISSUEOPENORDER:
            echoAction, echoData = self.getEchoOpenOrder( data )
            actionData.append( (echoAction, echoData) )
        elif nextAction ==  STRATSTATE.ISSUECLOSEORDER:
            echoAction, echoData = self.getEchoCancelOrder( data )
            actionData.append( (echoAction, echoData) )
            echoAction, echoData = self.getEchoCloseOrder( data )
            actionData.append( (echoAction, echoData) )
        else:
            msg = 'Uknown nextAction=%s' % nextAction
            logger.error(msg)
        self._actionData = actionData

    def snkPostUpdate(self, action, data):
        pass

    def srcPreUpdate(self, action, data):
        pass

    def srcPostUpdate(self, action, data):
        pass

    def newMsg(self):
        actionData = self._actionData
        self._actionData = None
        return actionData