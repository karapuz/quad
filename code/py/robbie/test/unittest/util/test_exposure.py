'''
AUTHOR      : ilya presman, 2016
TYPE:       : unittest
DESCRIPTION : util.exposure unittest module
DESCRIPTION : this module contains util.exposure tests
'''
import tempfile
import unittest
import robbie.util.exposure as utexp
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.echo.orderstate as orderstate
import robbie.echo.basestrat as basestrat
from   pprint import pprint as pp
import robbie.echo.policy as stratpolicy

import robbie.echo.onesession as onesession

class Test(unittest.TestCase):

    def test_1(self):
        path    = tempfile.mktemp() + '.csv'
        logger.debug('path=%s', path)
        owner   = 'ECHO1'
        exposure0 = {'ECHO1': [] }
        for target in ( 'SRC', 'SNK' ):
            for symbol in ['IBM', 'MSFT']:
                for shares in [100,200]:
                    for avgPrice in [101.1, 201.2]:
                        exposure0['ECHO1'].append((target, symbol, shares, avgPrice))
        utexp.dumpIntoCsv( path=path, exposure=exposure0)

        exposure1 = utexp.loadFromCsv(path)

        pp( exposure0 )
        pp( exposure1 )
        self.assertEqual(exposure0,exposure1)

        policy    = stratpolicy.ScaleVenueSpring1Policy( scale=.5, venue='GREY')
        echoStrat = onesession.Strategy(agent=owner, policy=policy)
        utexp.uploadIntoStrip(
                    agent    = owner,
                    exposure = exposure0,
                    strat    = echoStrat )

        exposure2 = utexp.collecFromStrip(agent=owner, strat=echoStrat)
        pp( exposure2 )

if __name__ == '__main__':
    unittest.main()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe -m unittest robbie.test.unittest.util.test_exposure
'''