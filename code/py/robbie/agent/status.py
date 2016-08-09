'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.agent module
'''

import argparse
import robbie.turf.util as turfutil
import robbie.util.libgui as libgui
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.echo.stratutil as stratutil
import robbie.echo.orderstate as orderstate

class OrderStatus(object):
    def __init__(self, domain):
        self._symbols    = symboldb.currentSymbols()
        self._symIds     = symboldb.symbol2id(self._symbols)
        self._maxNum     = symboldb._maxNum
        turf             = twkval.getenv('run_turf')
        mode             = turfutil.get(turf=turf, component='signal')
        if mode == stratutil.EXECUTION_MODE.NEW_FILL_CX:
            seePending = True
        elif mode == stratutil.EXECUTION_MODE.FILL_ONLY:
            seePending = False
        else:
            raise ValueError('Unknown mode=%s' % mode)

        with twkcx.Tweaks(run_domain=domain):
            self._orderstate = orderstate.OrderState(
                    readOnly    = True,
                    maxNum      = self._maxNum,
                    symbols     = self._symbols,
                    seePending  = seePending,
                    debug       = True )

    def asTable(self, header):
        return self._orderstate.asTable(header)

def run_status():
    agent     = twkval.getenv('agt_strat')
    srcOrders = OrderStatus('%s-src' % agent)
    snkOrders = OrderStatus('%s-snk' % agent)

    mat = srcOrders.asTable(header=['SRC'])
    mat.extend( snkOrders.asTable(header=['SNK']) )
    libgui.showTable( mat )

if __name__ == '__main__':
    '''
    -T turf
    -S strat
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-S", "--strat", help="strategy name", action="store")
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    args    = parser.parse_args()
    tweaks  = {
        'run_turf'  : args.turf,
        'agt_strat' : args.strat,
        'run_domain': 'echo_%s' % args.strat,
    }
    logger.debug( 'status: turf=%s strat=%s', args.turf, args.strat)
    with twkcx.Tweaks( **tweaks ):
        run_status()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\status.py --strat=ECHO1 --turf=dev


if 1:
    import robbie.tweak.context as twkcx
    import robbie.agent.status as agtstat
    reload( agtstat )

if 1:
    run_turf = 'dev',
    agt_strat = 'ECHO1',
    tweaks  = {
        'run_turf'  : run_turf,
        'agt_strat' : agt_strat,
        'run_domain': 'echo_%s' % agt_strat,
    }
    with twkcx.Tweaks( **tweaks ):
        s = agtstat.Status(agt_strat)

    print s._srcOrders._orderstate._pending

if 1:
    import robbie.echo.orderstate as orderstate
    reload(orderstate)

if 1:
    with open(r'c:\temp\a.csv', 'w') as fd:
        s._srcOrders._orderstate._nextNum = 10
        s._srcOrders._orderstate.dump(fd=fd, frmt='multiLine' )

'''
