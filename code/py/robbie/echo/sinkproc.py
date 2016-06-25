'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.sinkproc module
DESCRIPTION : this module contains order processing code
'''

import datetime
import robbie.fix.util as fut
from   robbie.util.logging import logger

def newOrderId():
    now = datetime.datetime.now()
    return now.strftime('SNK_%Y%m%d_%H%M%S')

def signal2order(app, action, data, senderCompID, targetCompID ):

    if action == 'new':
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
'''
