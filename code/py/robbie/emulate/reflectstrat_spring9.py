'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : emulate module
DESCRIPTION : this module contains strategy emulator
'''

import robbie.fix.util as fut
import robbie.util.calendar as cal
import robbie.tweak.context as twkcx
import robbie.util.logging as logging
from   robbie.util.logging import logger
import robbie.echo.policy as stratpolicy
from   robbie.echo.stratutil import STRATSTATE
import robbie.echo.reflectstrat_spring1 as strat

tweaks = {'env_loggerDir':r'c:\temp\%s' % cal.today(str)}
with twkcx.Tweaks(**tweaks):
    attrs = ( 'orderType', 'timeInForce', 'orderId', 'symbol', 'price', 'execTime', 'qty')
    tradeLogger = logging.FileLogger(name='spring9', attrs=attrs)

def newLeg(orderId, qty, price, action, s, mktPrice):
    srcData = {
        'orderType' : fut.Val_OrdType_Limit,
        'timeInForce' : fut.Val_TimeInForce_DAY,
        'orderId'   : orderId,
        'symbol'    : 'IBM',
        'price'     : price,
        'execTime'  : 1,
        'qty'       : qty,
    }
    tradeLogger.debug(label='newLeg',args=srcData)
    s.srcPreUpdate(action=action, data=srcData, mktPrice=mktPrice)
    s.srcUpdate(action=action, data=srcData, mktPrice=mktPrice)
    s.srcPostUpdate(action=action, data=srcData, mktPrice=mktPrice)

def run():
    agent   = 'ECHO1'
    policy  = stratpolicy.ScaleVenueSpring1Policy( scale=.5, venue='GREY')
    s       = strat.Strategy(agent=agent,policy=policy)

    #
    # open order 1
    #
    mktPrice = {'IBM': {'TRADE': 200, 'BID': 201, 'ASK': 199}}
    newLeg(orderId='OPEN_ORDER_1', qty=100, price=10, action=STRATSTATE.ORDERTYPE_NEW, s=s, mktPrice=mktPrice)
    newLeg(orderId='OPEN_ORDER_1', qty=100, price=10, action=STRATSTATE.ORDERTYPE_FILL, s=s, mktPrice=mktPrice)
    logger.debug( '1: SRC pending\n%s' % s.getCurrentState( target='SRC', where='all', which='pending', how='pandas'))

    tradeLogger.debug(label='newLeg',args=srcData)

    #
    # open order 2
    #
    newLeg(orderId='OPEN_ORDER_2', qty=200, price=10, action=STRATSTATE.ORDERTYPE_NEW, s=s, mktPrice=mktPrice)
    newLeg(orderId='OPEN_ORDER_2', qty=200, price=10, action=STRATSTATE.ORDERTYPE_FILL, s=s, mktPrice=mktPrice)
    logger.debug( '1: SRC pending\n%s' % s.getCurrentState( target='SRC', where='all', which='pending', how='pandas'))

    #
    # close order 2
    #
    newLeg(orderId='CLOSE_ORDER_4', qty=-200, price=12, action=STRATSTATE.ORDERTYPE_NEW, s=s, mktPrice=mktPrice)
    newLeg(orderId='CLOSE_ORDER_4', qty=-200, price=12, action=STRATSTATE.ORDERTYPE_FILL, s=s, mktPrice=mktPrice)
    logger.debug( '1: SRC pending\n%s' % s.getCurrentState( target='SRC', where='all', which='pending', how='pandas'))

    #
    # close order 1
    #
    newLeg(orderId='CLOSE_ORDER_3', qty=-100, price=11, action=STRATSTATE.ORDERTYPE_NEW, s=s, mktPrice=mktPrice)
    newLeg(orderId='CLOSE_ORDER_3', qty=-100, price=11, action=STRATSTATE.ORDERTYPE_FILL, s=s, mktPrice=mktPrice)
    logger.debug( '1: SRC pending\n%s' % s.getCurrentState( target='SRC', where='all', which='pending', how='pandas'))


    msgs = s.getActionData()
    logger.debug( '4: %s' % msgs )

    ##
    for actionData in msgs:
        target      = 'SNK'
        snkAction   = actionData['action']
        snkData     = actionData['data']

        s.snkPreUpdate(action=snkAction, data=snkData)
        s.snkUpdate(action=snkAction, data=snkData)
        s.snkPostUpdate(action=snkAction, data=snkData)

        logger.debug( '6: %s pending\n%s' % (target, s.getCurrentState( target=target, where='all', which='pending', how='pandas')))

    actionOrder = s.getActionOrders()
    logger.debug( '7: actionOrder=%s' % actionOrder )
    s.orderUpdate(actionOrder=actionOrder)

    msgs = s.getActionData()
    # logger.debug( '5: msgs=%s' % msgs )
    from pprint import pprint as pp
    pp(msgs)

if __name__ == '__main__':
    tweaks = {'env_loggerDir':r'c:\temp\%s' % cal.today(str)}
    with twkcx.Tweaks(**tweaks):
        run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\emulate\reflectstrat_spring9.py
'''