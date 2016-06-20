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
from   robbie.util.logging import logger

def run_agent():
    strat            = twkval.getenv('agt_strat')
    turf             = twkval.getenv('run_turf')
    agt_comm         = turfutil.get(turf=turf, component='communication', sub=strat)
    agent_execSrc    = agt_comm['agent_execSrc']
    port_sigCon      = agt_comm['agent_sigCon']
    agent_execSnkIn  = agt_comm['agent_execSnkIn']
    agent_execSnkOut = agt_comm['agent_execSnkOut']

    context = zmq.Context()

    reg_comm        = turfutil.get(turf=turf, component='communication', sub='SINK_REGISTER')
    reg_port        = reg_comm['port_reg']
    regConn         = context.socket(zmq.REQ)
    regConn.connect("tcp://localhost:%s" % reg_port)

    regConn.send('%s CanI?' % strat)
    ok              = regConn.recv()
    logger.debug('Can I login: %s', ok)

    agentSrcInCon       = context.socket(zmq.SUB)
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

    cmd = 'NEW'
    if cmd == 'NEW':
        logger.debug('NEW is sent')
        agentSinkOutCon.send('FAKE MESSAGE')

    # Process messages from both sockets
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
            msg = agentSrcInCon.recv() # process task
            print 'got message = ', msg
            agentSinkOutCon.send(msg)

        if agentSrcInCon in socks:
            msg = agentSrcInCon.recv() # process signal
            print 'got exec report = ', msg

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