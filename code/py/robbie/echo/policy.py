'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

import copy

class StratPolicy(object):
    pass

class ScaleVenuePolicy(StratPolicy):
    def __init__(self, scale, venue):
        self._scale = scale
        self._venue = venue

    def newOrder(self, orderId, data):
        qty     = data[ 'qty'   ]
        _venue  = data.get( 'venue' )
        d = copy.deepcopy(data)
        d[ 'orderId' ] = orderId
        d[ 'qty'     ] = int(self._scale * qty )
        d[ 'venue'   ] = self._venue
        return d

    def newCxOrder( self, orderId, origOrderId, origData ):
        qty     = origData[ 'qty'   ]
        _venue  = origData.get( 'venue' )
        d = copy.deepcopy(origData)
        d[ 'orderId'     ] = orderId
        d[ 'origOrderId' ] = origOrderId
        d[ 'qty'         ] = qty
        d[ 'venue'       ] = self._venue
        return d
