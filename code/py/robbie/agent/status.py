'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.agent module
'''

import json
import zmq
import argparse
import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.echo.reflectstrat as strat
import  robbie.util.symboldb as symboldb
import robbie.echo.orderstate as orderstate

class OrderStatus(object):
    def __init__(self, domain):
        self._symbols    = symboldb.currentSymbols()
        self._symIds     = symboldb.symbol2id(self._symbols)
        self._maxNum     = symboldb._maxNum

        with twkcx.Tweaks(run_domain=domain):
            self._orderstate = orderstate.OrderState(
                    readOnly    = True,
                    maxNum      = self._maxNum,
                    symIds      = self._symIds,
                    debug       = True )

class Status(object):

    def __init__(self, agent):
        self._agent     = agent
        self._srcOrders = OrderStatus('%s-src' % agent)
        self._snkOrders = OrderStatus('%s-snk' % agent)

def run_agent():
    agent            = twkval.getenv('agt_strat')
    turf             = twkval.getenv('run_turf')

    agt_comm         = turfutil.get(turf=turf, component='communication', sub=agent)

    agent_execSrc    = agt_comm['agent_execSrc']
    port_sigCon      = agt_comm['agent_sigCon']
    agent_execSnkIn  = agt_comm['agent_execSnkIn']
    agent_execSnkOut = agt_comm['agent_execSnkOut']

    snkRegPort       = turfutil.get(turf=turf, component='communication', sub='SNK_REG')['port_reg']
    srcRegPort       = turfutil.get(turf=turf, component='communication', sub='SRC_REG')['port_reg']

    echoStrat        = strat.Strategy(agent=agent)


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
        run_agent()

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
