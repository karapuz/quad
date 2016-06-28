'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : robbie.test.unittest.echo.test_stratutil.py
DESCRIPTION : this module contains unittest for echo.stratutil
'''

import unittest
from   robbie.util.logging import logger
import robbie.echo.stratutil as stratutil
from   robbie.echo.stratutil import STRATSTATE


class Test(unittest.TestCase):

    def test_1(self):
        state   =  STRATSTATE.OPENING
        sign    =  1
        qty     = -1
        nextState, action = stratutil.getAction(state=state, sign=sign, qty=qty)
        self.assertEqual(
            (nextState, action),
            (STRATSTATE.CLOSING, STRATSTATE.ISSUECLOSEORDER)
        )

    def test_2(self):
        state   =  STRATSTATE.OPENING
        sign    = -1
        qty     = -1
        nextState, action = stratutil.getAction(state=state, sign=sign, qty=qty)
        self.assertEqual(
            (nextState, action),
            (STRATSTATE.OPENING, STRATSTATE.ISSUEOPENORDER)
        )

    def test_3(self):
        state   =  STRATSTATE.CLOSING
        for sign in (-1, -1, 1, 1):
            for qty in (-1, 1, -1, 1):
                logger.debug('sign=%2d qty=%2d', sign, qty)
                nextState, action = stratutil.getAction(state=state, sign=sign, qty=qty)
                self.assertEqual(
                    (nextState, action),
                    (STRATSTATE.CLOSING, None)
                )


if __name__ == '__main__':
    unittest.main()

'''
robbie\test\unittest\echo\test_stratutil.py

c:\Python27\python2.7.exe -m unittest robbie.test.unittest

c:\Python27\python2.7.exe -m unittest robbie.test.unittest.echo.test_stratutil


'''