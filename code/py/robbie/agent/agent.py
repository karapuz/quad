'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.agent module
'''

import zmq
import argparse
import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
import robbie.util.symboldb as symboldb
from   robbie.util.logging import logger
import robbie.echo.orderstate as orderstate

class Agent(object):
    def __init__(self):
        self._symbols    = symboldb.currentSymbols()
        self._symIds     = symboldb.symbol2id(self._symbols)
        self._maxNum     = symboldb._maxNum
        self._orderstate = orderstate.OrderState(
                readOnly    = False,
                maxNum      = self._maxNum,
                symIds      = self._symIds,
                debug       = True )

    def onNew(self, execTime, orderId, symbol, qty, price):
        if self._orderstate.checkExistTag(orderId):
            self._orderstate.addError(status='DUPLICATE_NEW', data=(signalName, execTime, orderId, symbol, qty, price), msg='DUPLICATE_NEW')
            msg = 'Duplicate new for orderId=%s symbol=%s qty=%s' % (orderId, symbol, qty)
            logger.error(msg)
            return
        data = (execTime, orderId, symbol, qty, price)
        logger.debug('agent onNew:%s' % str(data))
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addPendingByIx(ix=ixs,vals=(qty,qty))

    def onFill(self, execTime, orderId, symbol, qty, price):
        data = execTime, orderId, symbol, qty, price
        logger.debug('agent onFill:%s' % str(data))
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addRealizedByIx(ix=ixs,vals=(qty,qty))

    def onCxRx(self, execTime, orderId, symbol, qty):
        msgd = (execTime, orderId, symbol, qty)
        logger.debug('agent onCxRx:%s' % str(data))
        ixs = self._orderstate.addTags((symbol, orderId))
        self._orderstate.addCanceledByIx(ix=ixs,vals=(qty,qty))

def run_agent():
    strat            = twkval.getenv('agt_strat')
    turf             = twkval.getenv('run_turf')

    agt_comm         = turfutil.get(turf=turf, component='communication', sub=strat)

    agent_execSrc    = agt_comm['agent_execSrc']
    port_sigCon      = agt_comm['agent_sigCon']
    agent_execSnkIn  = agt_comm['agent_execSnkIn']
    agent_execSnkOut = agt_comm['agent_execSnkOut']

    reg_comm        = turfutil.get(turf=turf, component='communication', sub='SINK_REGISTER')
    reg_port        = reg_comm['port_reg']

    context         = zmq.Context()
    regConn         = context.socket(zmq.REQ)
    regConn.connect("tcp://localhost:%s" % reg_port)

    regConn.send('%s: can i?' % strat)
    ok = regConn.recv()
    logger.debug('can i login?: %s', ok)

    agentSrcInCon       = context.socket(zmq.SUB)
    agentSrcInCon.setsockopt(zmq.SUBSCRIBE, b'')
    agentSrcInCon.connect('tcp://localhost:%s' % agent_execSrc)

    sigCon = context.socket(zmq.SUB)
    sigCon.setsockopt(zmq.SUBSCRIBE, b'')
    sigCon.connect('tcp://localhost:%s' % port_sigCon)

    agentSinkOutCon      = context.socket(zmq.PAIR) # PUB
    agentSinkOutCon.bind('tcp://*:%s' % agent_execSnkOut)

    agentSinkInCon       = context.socket(zmq.PAIR) # SUB
    agentSinkInCon.connect('tcp://localhost:%s' % agent_execSnkIn)

    # Initialize poll set
    poller = zmq.Poller()
    poller.register(sigCon,         zmq.POLLIN)
    poller.register(agentSrcInCon,  zmq.POLLIN)
    poller.register(agentSinkInCon, zmq.POLLIN)

    while True:
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if sigCon in socks:
            msg = sigCon.recv() # process signal
            print 'got signal = ', msg
            break

        if agentSinkInCon in socks:
            msg = agentSinkInCon.recv() # process task
            print 'got message = ', msg

        if agentSrcInCon in socks:
            msg = agentSrcInCon.recv() # process signal
            print 'got exec report = ', msg
            print 'some complext strat proc = ', msg
            agentSinkOutCon.send(msg)

'''
form sink =  {
    "orderId"    : "20160621_182343",
    "action"     : "new",
    "execTime"   : "20160621-22:23:43.556",
    "price"      : 0,
    "signalName" : "ECHO1",
    "symbol"     : "IBM",
    "qty"        : 1000}

from src  =  {
    "orderId"    : "20160621_182343",
    "action"     : "fill",
    "execTime"   : "TIME",
    "price"      : 200.0,
    "signalName" : "ECHO1",
    "symbol"     : "IBM",
    "qty"        : 200}

'''
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
    logger.debug( 'agent: turf=%s strat=%s', args.turf, args.strat)
    with twkcx.Tweaks( **tweaks ):
        run_agent()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\agent.py --strat=ECHO1 --turf=dev

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\agent.py --strat=ECHO2 --turf=dev
'''