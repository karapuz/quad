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

    data = {
        'orderId'   : 'ORDER_1',
        'symbol'    : 'IBM',
        'price'     : 10,
        'execTime'  : 1,
        'qty'       : 100,
    }
    action=STRATSTATE.ORDERTYPE_NEW
    s.srcPreUpdate(action=action, data=data)
    s.srcUpdate(action=action, data=data)
    s.srcPostUpdate(action=action, data=data)

    logger.debug( '1: SRC pending\n%s' % s.getCurrentState( target='SRC', where='all', which='pending', how='pandas'))

    action=STRATSTATE.ORDERTYPE_FILL
    s.srcPreUpdate(action=action, data=data)
    s.srcUpdate(action=action, data=data)
    s.srcPostUpdate(action=action, data=data)

    logger.debug( '2: SRC pending\n%s' % s.getCurrentState( target='SRC', where='all', which='pending', how='pandas'))
    logger.debug( '3: SRC realized\n%s' % s.getCurrentState( target='SRC', where='all', which='realized', how='pandas'))

    symbol = data['symbol']
    #orders = s.getOrdersForSymbol(symbol)
    msgs = s.getActionData()
    logger.debug( '4: %s' % msgs )

    ##
    for actionData in msgs:
        authAction = actionData['action']
        data       = actionData['data']

        action  = STRATSTATE.ORDERTYPE_NEW
        target  = 'SNK'

        s.snkPreUpdate(action=action, data=data)
        s.snkUpdate(action=action, data=data)
        s.snkPostUpdate(action=action, data=data)

        logger.debug( '6: SRC pending\n%s' % s.getCurrentState( target=target, where='all', which='pending', how='pandas'))

        action=STRATSTATE.ORDERTYPE_FILL
        s.snkPreUpdate(action=action, data=data)
        s.snkUpdate(action=action, data=data)
        s.snkPostUpdate(action=action, data=data)

        logger.debug( '7: SNK pending\n%s' % s.getCurrentState( target=target, where='all', which='pending', how='pandas'))
        logger.debug( '8: SNK realized\n%s' % s.getCurrentState( target=target, where='all', which='realized', how='pandas'))
        logger.debug( '9: %s' % s.getActionData() )

if __name__ == '__main__':
    run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\emulate\reflectstrat_spring3.py
'''