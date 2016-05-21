'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.execsrc module
'''

import zmq
import time
import argparse
import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger

def run_execsrc():
    # Prepare our context and sockets
    context     = zmq.Context()
    strat       = twkval.getenv('agt_strat')
    turf        = twkval.getenv('run_turf')
    agt_comms   = turfutil.get(turf=turf, component='communication')

    # Connect to task ventilator
    conns   = []
    sigs    = []
    for agent, agt_comm in agt_comms.iteritems():
        logger.debug( 'execsrc: agent=%s', agent)
        port_execSrc    = agt_comm['port_execSrc']
        port_sigCon     = agt_comm['port_sigCon']

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port_execSrc)
        conns.append( c )

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port_sigCon)
        sigs.append( c )

    # Process messages from both sockets
    for ix in xrange(1000):
        for c in conns:
            msg = '%d' % ix
            c.send( msg ) # process task
            print 'sending msg =', msg
    time.sleep(10)
    for c in sigs:
        c.send( '%d' % ix ) # process task

if __name__ == '__main__':
    '''
    -T turf
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    args    = parser.parse_args()
    tweaks  = {
        'run_turf'  : args.turf,
    }
    logger.debug( 'agent: turf=%s', args.turf)
    with twkcx.Tweaks( **tweaks ):
        run_execsrc()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\execsrc.py --turf=dev

'''
