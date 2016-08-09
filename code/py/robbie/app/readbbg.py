'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.agent module
'''

import time
import random
import argparse
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.util.pricestriputil as pricestriputil

def run():
    turf    = twkval.getenv('run_turf')
    bbg     = pricestriputil.createPriceStrip(turf=turf, readOnly=True)
    symbols = symboldb.currentSymbols()

    while 1:
        time.sleep(1)
        y = []
        for symbol in symbols:
            x = bbg.getInstantPriceByName(priceType='TRADE', symbol=symbol)
            y.append(x)
        logger.debug(str(y))

if __name__ == '__main__':
    '''
    -T turf
    -S strat
    -C command
    -A arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-T", "--turf",  help="turf name", action="store")

    args    = parser.parse_args()
    tweaks  = {
        'run_turf'  : args.turf,
    }
    logger.debug( 'fake bbg: turf=%s', args.turf)
    with twkcx.Tweaks( **tweaks ):
        run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\app\readbbg.py --turf=dev
'''