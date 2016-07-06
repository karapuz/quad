'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.sinkproc module
DESCRIPTION : this module contains order processing code
'''

import datetime
import robbie.fix.util as fut
from   robbie.echo.stratutil import STRATSTATE
from   robbie.util.logging import logger

def newOrderId():
    now = datetime.datetime.now()
    return now.strftime('SNK_%Y%m%d_%H%M%S')

def signal2order(app, action, data, senderCompID, targetCompID ):

    if action  == STRATSTATE.ORDERTYPE_NEW:
        account = data['signalName']
        symbol  = data['symbol']
        qty     = int(data['qty'])
        price   = float(data['price'])

        app.sendOrder(
            senderCompID = senderCompID,
            targetCompID = targetCompID,
            account      = account,
            orderId      = newOrderId(),
            symbol       = symbol,
            qty          = qty,
            price        = price,
            timeInForce  = fut.Val_TimeInForce_DAY,
            tagVal       = None )

    elif action  == STRATSTATE.ORDERTYPE_CXRX:
        account = data['signalName']
        symbol  = data['symbol']
        qty     = int(data['qty'])

        app.sendOrder(
            senderCompID = senderCompID,
            targetCompID = targetCompID,
            account      = account,
            orderId      = newOrderId(),
            symbol       = symbol,
            qty          = qty,
            tagVal       = None )
    else:
        logger.error('SINKPROC: Unknown action=%s data=%s', action, str(data))
'''
agentOut =  {
    "orderId"    : "20160621_075324",
    "action"     : "new",
    "execTime"   : "20160621-11:53:24.451",
    "price"      : 0,
    "signalName" : "ECHO1",
    "symbol"     : "IBM",
    "qty"        : 1000
}

ERROR EXECSINKAPP: skip
    action=ORDER TYPE NEW for
    msg={
        u'action': u'ORDER TYPE NEW',
        u'data': {
            u'orderId'      : u'ECHO_20160702_145031_1',
            u'execTime'     : u'20160702-18:50:31.362',
            u'orderType'    : u'2',
            u'price'        : 0,
            u'venue'        : u'GREY',
            u'qty'          : 500,
            u'symbol'       : u'IBM',
            u'signalName'   : u'ECHO1'
            }
        }
'''
