'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : robbie.test.unittest.echo.test_stratutil.py
DESCRIPTION : this module contains unittest for echo.orderstate
'''

import unittest
from   robbie.util.logging import logger
import robbie.echo.orderstate as orderstate

def setUp():
    readOnly    = False
    maxNum      = 1000
    symbols     = ('A', 'B', 'C', 'D')
    seePending  = True
    debug       = True
    return orderstate.OrderState( readOnly=readOnly, maxNum=maxNum, symbols=symbols, seePending=seePending, debug=debug )


class Test(unittest.TestCase):

    def test_1(self):
        orderState  = setUp()
        orderId     = 'ORDER1'
        symbol      = 'A'
        vals        = [100, 100]
        ixs         = orderState.addTags((symbol, orderId))
        orderState.addPendingByIx(ix=ixs, vals=vals, checked=True, verbose=False )
        self.assertTrue( all( orderState.getPendingByIx(ixs) == vals ) )

    def test_2(self):
        orderState  = setUp()
        orderId     = 'ORDER1'
        symbol      = 'A'
        vals        = [100, 100]
        ixs         = orderState.addTags((symbol, orderId))
        orderState.addPendingByIx(ix=ixs, vals=vals, checked=True, verbose=False )
        orderId     = 'ORDER2'
        symbol      = 'A'
        vals        = [100, 100]
        ixs         = orderState.addTags((symbol, orderId))
        orderState.addPendingByIx(ix=ixs, vals=vals, checked=True, verbose=False )
        combined    = orderState.getPendingByIx(ixs)
        self.assertTrue( all( combined == [200,100] ) )

    def test_3(self):
        orderState  = setUp()
        orderId     = 'ORDER1'
        symbol      = 'A'
        vals        = [100, 100]
        ixs         = orderState.addTags((symbol, orderId))
        orderState.addPendingByIx(ix=ixs, vals=vals, checked=True, verbose=False )

        orderId     = 'ORDER2'
        symbol      = 'A'
        vals        = [-100, -100]
        ixs         = orderState.addTags((symbol, orderId))
        orderState.addPendingByIx(ix=ixs, vals=vals, checked=True, verbose=False )

        combined    = orderState.getPendingByIx(ixs)
        self.assertTrue( all( combined == [0,-100] ) )

if __name__ == '__main__':
    unittest.main()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe -m unittest robbie.test.unittest.echo.test_orderstate
'''