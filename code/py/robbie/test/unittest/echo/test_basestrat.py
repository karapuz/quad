'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : robbie.test.unittest.echo.test_stratutil.py
DESCRIPTION : this module contains unittest for echo.stratutil
'''

import unittest
import robbie.echo.policy as stratpolicy
from   robbie.util.logging import logger
import robbie.echo.reflectstrat as strat
from   robbie.echo.stratutil import STRATSTATE


class Test(unittest.TestCase):

    def test_1(self):
        agent     = 'ECHO1'
        policy    = stratpolicy.ScaleVenuePolicy( scale=.5, venue='GREY')
        echoStrat = strat.Strategy(agent=agent, policy=policy)

        def srcStep(cmd):
            action  = cmd[ 'action' ]
            data    = cmd[ 'data'   ]

            logger.debug('srcStep: %s %s', action, data)
            echoStrat.srcPreUpdate(action=action, data=data)
            echoStrat.srcUpdate(action=action, data=data)
            echoStrat.srcPostUpdate(action=action, data=data)
            return echoStrat.getActionData()

        def procSnkMsgs(msgs):
            for msg in msgs:
                action = msg[ 'action']
                data   = msg[ 'data'  ]

                logger.debug('snkStep: %s %s', action, data)
                echoStrat.snkPreUpdate(action=action, data=data)
                echoStrat.snkUpdate(action=action, data=data)
                echoStrat.snkPostUpdate(action=action, data=data)

        cmd1 = {
            'action': STRATSTATE.ORDERTYPE_NEW,
            'data': {
                'symbol'    : 'IBM',
                'qty'       : 1000,
                'orderId'   : 'SRC_ORDER_1',
                'execTime'  : 'NOW',
                'price'     : 100,
            }
        }

        msgs = srcStep(cmd1)
        procSnkMsgs(msgs)

        cmd2 = {
            'action': STRATSTATE.ORDERTYPE_CXRX,
            'data': {
                'symbol'    : 'IBM',
                'qty'       : 1000,
                'orderId'       : 'SRC_CX_ORDER_1',
                'origOrderId'   : 'SRC_ORDER_1',
                'execTime'  : 'NOW',
                'price'     : 100,
            }
        }

        msgs = srcStep(cmd2)
        procSnkMsgs(msgs)

if __name__ == '__main__':
    unittest.main()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe -m unittest robbie.test.unittest.echo.test_basestrat

'''