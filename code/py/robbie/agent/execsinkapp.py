'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.execsrc module
'''

import zmq
import json
import time
import argparse
import datetime
import robbie.fix.util as fut
import robbie.echo.core as echocore
import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.execution.execsrclink as execsrclink
import robbie.execution.messageadapt as messageadapt

def newOrderId():
    now = datetime.datetime.now()
    return now.strftime('%Y%m%d_%H%M%S')

def toVal(k,v):
    return str(v)

def toStr(c):
    nc = {}
    for k,v in c.iteritems():
        nc[str(k)] = toVal(k,v)
    return nc

def run_execsrc():
    context     = zmq.Context()
    turf        = twkval.getenv('run_turf')
    agt_comms   = turfutil.get(turf=turf, component='communication')
    agt_list    = turfutil.get(turf=turf, component='agents')

    poller      = zmq.Poller()
    reg_port    = agt_comms['SINK_REGISTER']['port_reg']
    regConn     = context.socket(zmq.REP)
    regConn.bind("tcp://*:%s" % reg_port)
    poller.register(regConn, zmq.POLLIN)

    agentIn     = {}
    agentOut    = {}
    sigs        = []

    for agent, agt_comm in agt_comms.iteritems():
        if agent not in agt_list:
            logger.debug('not an agent: %s', agent)
            continue
        logger.debug( 'execsink: agent=%s', agent)

        agent_execSnkIn  = agt_comm['agent_execSnkIn']
        agent_execSnkOut = agt_comm['agent_execSnkOut']

        sinkOutCon = context.socket(zmq.PAIR) # PUB
        sinkOutCon.bind('tcp://*:%s' % agent_execSnkIn)

        sinkInCon = context.socket(zmq.PAIR) # SUB
        sinkInCon.connect('tcp://localhost:%s' % agent_execSnkOut)

        poller.register(sinkInCon, zmq.POLLIN)
        agentIn [ agent ] = sinkInCon
        agentOut[ agent ] = sinkOutCon

    # signalStrat = echocore.SignalStrat(conns)
    # msgAdapter  = messageadapt.Message(['ECHO1','ECHO1'], 'TIME')
    # appThread, thread = execsrclink.init(signalStrat=signalStrat,msgAdapter=msgAdapter)
    # app = appThread.getApplication()

    # Process messages from both sockets
    while True:
        logger.debug('in the loop')
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        for agent, c in agentIn.iteritems():
            if c in socks:
                msg = c.recv() # process signal
                print 'agentOut = ', msg
                agentOut[ agent ].send('GOT agent=%s' % agent)

        if regConn in socks:
            msg = regConn.recv()
            regConn.send('Ok')
            print 'registered[sink] = ', msg

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
    logger.debug( 'execsinkapp: turf=%s', args.turf)
    with twkcx.Tweaks( **tweaks ):
        run_execsrc()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\execsinkapp.py --turf=dev
'''
