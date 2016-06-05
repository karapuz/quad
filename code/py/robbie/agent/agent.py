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
    # Prepare our context and sockets
    strat           = twkval.getenv('agt_strat')
    turf            = twkval.getenv('run_turf')

    agt_comm        = turfutil.get(turf=turf, component='communication', sub=strat)

    port_execSrc    = agt_comm['port_execSrc']
    port_sigCon     = agt_comm['port_sigCon']
    #port_execSnkIn  = agt_comm['port_execSnkIn']
    #port_execSnkOut = agt_comm['port_execSnkOut']

    context = zmq.Context()
    dataCon = context.socket(zmq.SUB)
    dataCon.setsockopt(zmq.SUBSCRIBE, b'')
    dataCon.connect('tcp://localhost:%s' % port_execSrc)

    sigCon = context.socket(zmq.SUB)
    sigCon.setsockopt(zmq.SUBSCRIBE, b'')
    sigCon.connect('tcp://localhost:%s' % port_sigCon)

    # Initialize poll set
    poller = zmq.Poller()
    poller.register(dataCon, zmq.POLLIN)
    poller.register(sigCon,  zmq.POLLIN)

    # Process messages from both sockets
    while True:
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if dataCon in socks:
            msg = dataCon.recv() # process task
            print 'got message = ', msg
        if sigCon in socks:
            msg = sigCon.recv() # process weather update
            print 'got signal = ', msg
            break

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