'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategy emulator
'''

from   robbie.util.logging import logger
import robbie.echo.policy as stratpolicy
from   robbie.echo.stratutil import STRATSTATE
import robbie.echo.reflectstrat_spring1 as strat

def run():
    agent   = 'ECHO1'
    policy  = stratpolicy.ScaleVenuePolicy( scale=.5, venue='GREY')
    s       = strat.Strategy(agent=agent,policy=policy)

    srcData = {
        'orderId'   : 'ORDER_1',
        'symbol'    : 'IBM',
        'price'     : 10,
        'execTime'  : 1,
        'qty'       : 100,
    }
    srcAction   = STRATSTATE.ORDERTYPE_NEW
    s.srcPreUpdate(action=srcAction, data=srcData)
    s.srcUpdate(action=srcAction, data=srcData)
    s.srcPostUpdate(action=srcAction, data=srcData)

    logger.debug( '1: SRC pending\n%s' % s.getCurrentState( target='SRC', where='all', which='pending', how='pandas'))

    action=STRATSTATE.ORDERTYPE_FILL
    s.srcPreUpdate(action=action, data=srcData)
    s.srcUpdate(action=action, data=srcData)
    s.srcPostUpdate(action=action, data=srcData)

    msgs = s.getActionData()
    logger.debug( '4: %s' % msgs )

    ##
    for actionData in msgs:
        target      = 'SNK'
        snkAction   = actionData['action']
        snkData     = actionData['data']

        #snkAction  = STRATSTATE.ORDERTYPE_NEW

        s.snkPreUpdate(action=snkAction, data=snkData)
        s.snkUpdate(action=snkAction, data=snkData)
        s.snkPostUpdate(action=snkAction, data=snkData)

        logger.debug( '6: %s pending\n%s' % (target, s.getCurrentState( target=target, where='all', which='pending', how='pandas')))

    actionOrder = s.getActionOrders()
    logger.debug( '7: actionOrder=%s' % actionOrder )
    s.orderUpdate(actionOrder=actionOrder)

    msgs = s.getActionData()
    logger.debug( '5: msgs=%s' % msgs )

if __name__ == '__main__':
    run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\emulate\reflectstrat_spring4.py
'''