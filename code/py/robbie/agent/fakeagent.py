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

def run_agent(cmd, args):
    # Prepare our context and sockets
    strat           = twkval.getenv('agt_strat')
    turf            = twkval.getenv('run_turf')

    agt_comm        = turfutil.get(turf=turf, component='communication', sub=strat)

    agent_execSnkOut = agt_comm['agent_execSnkOut']
    agent_execSnkIn  = agt_comm['agent_execSnkIn']

    context         = zmq.Context()
    sinkOutCon      = context.socket(zmq.PAIR) # PUB
    sinkOutCon.bind('tcp://*:%s' % agent_execSnkOut)

    sinkInCon = context.socket(zmq.PAIR) # SUB
    sinkInCon.connect('tcp://localhost:%s' % agent_execSnkIn)

    reg_comm        = turfutil.get(turf=turf, component='communication', sub='SINK_REGISTER')
    reg_port        = reg_comm['port_reg']
    regConn         = context.socket(zmq.REQ)
    regConn.connect("tcp://localhost:%s" % reg_port)

    regConn.send('CanI?')
    ok = regConn.recv()
    logger.debug('Can I login: %s', ok)

    poller = zmq.Poller()
    poller.register(sinkInCon, zmq.POLLIN)

    if cmd == 'NEW':
        logger.debug('NEW is sent')
        sinkOutCon.send('FAKE MESSAGE')
        # import time
        # time.sleep(5)
        # return

    # Process messages from both sockets
    while True:
        logger.debug('in the loop')
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if sinkInCon in socks:
            msg = sinkInCon.recv() # process signal
            print 'got signal = ', msg
            break

if __name__ == '__main__':
    '''
    -T turf
    -S strat
    -C command
    -A arguments
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-S", "--strat", help="strategy name", action="store")
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    parser.add_argument("-A", "--args",  help="arguments", action="store")
    parser.add_argument("-C", "--cmd",  help="command", action="store")

    args    = parser.parse_args()
    tweaks  = {
        'run_turf'  : args.turf,
        'agt_strat' : args.strat,
    }
    logger.debug( 'fake agent: turf=%s strat=%s', args.turf, args.strat)
    with twkcx.Tweaks( **tweaks ):
        run_agent(args.cmd, args.args)

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\fakeagent.py --strat=ECHO1 --turf=dev --cmd=NEW
'''