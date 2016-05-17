'''
TYPE        : lib
OWNER       : ilya
DESCRIPTION : order id generator
'''

import datetime

def idGen( prefix ):
    i   = 0
    now = datetime.datetime.now()
    p   = now.strftime( '%Y%m%d%H%M%S' )
    while 1:
        i += 1
        yield '%s_%s_%d' % ( p, prefix, i)

newTradeId = idGen('NewOrder')
