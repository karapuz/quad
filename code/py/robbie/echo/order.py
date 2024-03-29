'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.order module
DESCRIPTION : this module contains strategies
'''

class EchoOrder(object):
    '''  '''
    def __init__(self, openOrder):
        self._openOrder     = openOrder
        self._closeOrder    = None

    def addCloseOrder(self, closeOrder):
        self._closeOrder = closeOrder

    def getOpenOrder(self):
        return self._openOrder

    def getCloseOrder(self):
        return self._closeOrder

    def _repr(self):
        return 'order.EchoOrder (open=%s, close=%s)' % (self._openOrder['orderId'], self._closeOrder['orderId'] if self._closeOrder else 'None')

    __str__ = _repr
    __repr__ = _repr

class EchoTradeSession(object):
    '''  '''
    def __init__(self, openOrder):
        self._legs = [ openOrder ]

    def addLeg(self, leg):
        self._legs.append( leg )

    def getLegs(self):
        return self._legs

    def _repr(self):
        return 'order.EchoTradeSession(legs#=%d, legs=%s)' % ( len(self._legs), [ l['orderId'] for l in self._legs] )

    __str__ = _repr
    __repr__ = _repr
