'''
AUTHOR      : ilya presman, 2016
TYPE:       : unit test
DESCRIPTION : this module contains unittest for echo.orderstate
'''

import unittest
from   robbie.util.logging import logger
import robbie.echo.orderstate as orderstate

def setUp(seePending):
    readOnly    = False
    maxNum      = 1000
    symbols     = ('A', 'B', 'C', 'D')
    seePending  = seePending
    debug       = True
    return orderstate.OrderState( readOnly=readOnly, maxNum=maxNum, symbols=symbols, seePending=seePending, debug=debug )


class Test(unittest.TestCase):

    def test_1_0(self):
        orderId     = 'ORDER1'
        symbol      = 'A'
        vals        = [100, 100]

        orderState  = setUp(seePending=True)
        ixs         = orderState.addTags((symbol, orderId))
        orderState.addPendingByIx(ix=ixs, vals=vals, checked=True, verbose=False )
        self.assertTrue( all( orderState.getPendingByIx(ixs) == vals ) )

    def test_1_1(self):
        orderId     = 'ORDER1'
        symbol      = 'A'
        vals        = [100, 100]

        orderState  = setUp(seePending=False)
        ixs         = orderState.addTags((symbol, orderId))
        orderState.addPendingByIx(ix=ixs, vals=vals, checked=True, verbose=False )
        self.assertTrue( all( orderState.getPendingByIx(ixs) == vals ) )

    def test_2(self):
        orderState  = setUp(seePending=True)
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


    def _test_3(self, orderState):

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

        symQty = orderState.getLivePendingIxBySymbol(symbol='A')
        self.assertEqual( {'ORDER2': -100.0, 'ORDER1': 100.0}, symQty )

        orderId     = 'ORDER3'
        symbol      = 'B'
        vals        = [100, 100]
        ixs         = orderState.addTags((symbol, orderId))
        orderState.addPendingByIx(ix=ixs, vals=vals, checked=True, verbose=False )

        orderId     = 'ORDER4'
        symbol      = 'B'
        vals        = [-100, -100]
        ixs         = orderState.addTags((symbol, orderId))
        orderState.addPendingByIx(ix=ixs, vals=vals, checked=True, verbose=False )

        symQty = orderState.getLivePendingIxBySymbol(symbol='B')
        self.assertEqual( {'ORDER4': -100.0, 'ORDER3': 100.0}, symQty )

        symQty = orderState.getLivePendingIxBySymbol(symbol='A')
        self.assertEqual( {'ORDER2': -100.0, 'ORDER1': 100.0}, symQty )

        orderId     = 'ORDER4'
        symbol      = 'B'
        vals        = [-100, -100]
        ixs         = orderState.addTags((symbol, orderId))
        orderState.addRealizedByIx(ix=ixs, vals=vals, checked=True, verbose=False )

        symQty = orderState.getLivePendingIxBySymbol(symbol='B')
        self.assertEqual( {'ORDER3': 100.0}, symQty )

    def test_31(self):
        orderState  = setUp(seePending=True)
        self._test_3(orderState=orderState)

    def test_32(self):
        orderState  = setUp(seePending=False)
        self._test_3(orderState=orderState)

if __name__ == '__main__':
    unittest.main()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe -m unittest robbie.test.unittest.echo.test_orderstate
'''