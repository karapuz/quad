'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : emulate module
DESCRIPTION : this module contains strategy emulator
'''

import robbie.fix.util as fut
import robbie.tweak.value as twkval
import robbie.util.filelogging as flogging
from   robbie.util.logging import logger
import robbie.echo.policy as stratpolicy
from   robbie.echo.stratutil import STRATSTATE
import robbie.echo.reflectstrat_spring1 as strat

name        = 'spring10'
domain      = twkval.getenv('run_domain')
user        = twkval.getenv('env_userName')
session     = twkval.getenv('run_session')
attrs       = ( 'orderType', 'timeInForce', 'orderId', 'symbol', 'price', 'execTime', 'qty')
vars        = dict( domain=domain, user=user, session=session, name=name, attrs=attrs )
tradeLogger = flogging.getFileLogger(**vars)

def newLeg(orderId, qty, price, action, s, mktPrice):
    srcData = {
        'orderType'     : fut.Val_OrdType_Limit,
        'timeInForce'   : fut.Val_TimeInForce_DAY,
        'orderId'       : orderId,
        'symbol'        : 'IBM',
        'price'         : price,
        'execTime'      : 1,
        'qty'           : qty,
    }
    tradeLogger.debug(label='newLeg',args=srcData)
    s.srcPreUpdate(action=action, data=srcData, mktPrice=mktPrice)
    s.srcUpdate(action=action, data=srcData, mktPrice=mktPrice)
    s.srcPostUpdate(action=action, data=srcData, mktPrice=mktPrice)

def fill(s):
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

        tradeLogger.debug(label='newSink',args=snkData)

        snkAction   = STRATSTATE.ORDERTYPE_FILL

        s.snkPreUpdate(action=snkAction, data=snkData)
        s.snkUpdate(action=snkAction, data=snkData)
        s.snkPostUpdate(action=snkAction, data=snkData)

        tradeLogger.debug(label='fillSink',args=snkData)

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

    fill(s)

    #
    # open order 2
    #
    newLeg(orderId='OPEN_ORDER_2', qty=200, price=10, action=STRATSTATE.ORDERTYPE_NEW, s=s, mktPrice=mktPrice)
    newLeg(orderId='OPEN_ORDER_2', qty=200, price=10, action=STRATSTATE.ORDERTYPE_FILL, s=s, mktPrice=mktPrice)
    logger.debug( '1: SRC pending\n%s' % s.getCurrentState( target='SRC', where='all', which='pending', how='pandas'))

    fill(s)

    #
    # close order 2
    #
    newLeg(orderId='CLOSE_ORDER_4', qty=-200, price=12, action=STRATSTATE.ORDERTYPE_NEW, s=s, mktPrice=mktPrice)
    newLeg(orderId='CLOSE_ORDER_4', qty=-200, price=12, action=STRATSTATE.ORDERTYPE_FILL, s=s, mktPrice=mktPrice)
    logger.debug( '1: SRC pending\n%s' % s.getCurrentState( target='SRC', where='all', which='pending', how='pandas'))

    fill(s)

    #
    # close order 1
    #
    newLeg(orderId='CLOSE_ORDER_3', qty=-100, price=11, action=STRATSTATE.ORDERTYPE_NEW, s=s, mktPrice=mktPrice)
    newLeg(orderId='CLOSE_ORDER_3', qty=-100, price=11, action=STRATSTATE.ORDERTYPE_FILL, s=s, mktPrice=mktPrice)
    logger.debug( '1: SRC pending\n%s' % s.getCurrentState( target='SRC', where='all', which='pending', how='pandas'))

    fill(s)

    actionOrder = s.getActionOrders()
    logger.debug( '7: actionOrder=%s' % actionOrder )
    s.orderUpdate(actionOrder=actionOrder)

if __name__ == '__main__':
    run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\emulate\reflectstrat_spring10.py
'''