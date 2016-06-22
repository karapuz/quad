'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.execsrc module
'''

import zmq
import json
import time
import argparse
import robbie.echo.core as echocore
import robbie.echo.sinkproc as sinkproc

import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.execution.execsrclink as execsrclink
import robbie.execution.messageadapt as messageadapt


def toVal(k,v):
    return str(v)

def toStr(c):
    nc = {}
    for k,v in c.iteritems():
        nc[str(k)] = toVal(k,v)
    return nc

def run_execSink():
    context     = zmq.Context()
    turf        = twkval.getenv('run_turf')
    agt_comms   = turfutil.get(turf=turf, component='communication')
    agt_list    = turfutil.get(turf=turf, component='agents')

    poller      = zmq.Poller()
    reg_port    = agt_comms['SINK_REGISTER']['port_reg']
    regConn     = context.socket(zmq.REP)
    regConn.bind("tcp://*:%s" % reg_port)
    poller.register(regConn, zmq.POLLIN)

    cmd_port    = agt_comms['SINKCMD']['port_cmd']
    cmdConn     = context.socket(zmq.REP)
    cmdConn.bind("tcp://*:%s" % cmd_port)
    poller.register(cmdConn, zmq.POLLIN)

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

        agentSinkIntCon = context.socket(zmq.PAIR) # PUB
        agentSinkIntCon.bind('tcp://*:%s' % agent_execSnkIn)

        agentSinkOutCon = context.socket(zmq.PAIR) # SUB
        agentSinkOutCon.connect('tcp://localhost:%s' % agent_execSnkOut)

        poller.register(agentSinkOutCon, zmq.POLLIN)
        agentIn [ agent ] = agentSinkIntCon
        agentOut[ agent ] = agentSinkOutCon

    signalStrat = echocore.SignalStrat(agentIn)
    msgAdapter  = messageadapt.Message(['ECHO1','ECHO1'], 'TIME')
    tweakName   = 'fix_SinkConnConfig'
    appThread, thread = execsrclink.init(
                            tweakName   = tweakName,
                            signalStrat = signalStrat,
                            msgAdapter  = msgAdapter)

    app          = appThread.getApplication()
    commCreds    = twkval.getenv( tweakName )
    senderCompID = commCreds[ 'sender' ]
    targetCompID = commCreds[ 'target' ]

    # Process messages from both sockets
    while True:
        logger.debug('in the loop')
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        for agent, c in agentOut.iteritems():
            if c in socks:
                cmds    = c.recv() # process signal
                cmd     = json.loads(cmds)
                cmd     = toStr(cmd)
                action  = cmd['action']

                if action == 'new':
                    logger.debug('agentOut msg = %s', cmd)
                    sinkproc.signal2order(
                        app          = app,
                        cmd          = cmd,
                        senderCompID = senderCompID,
                        targetCompID = targetCompID )
                else:
                    msg = 'skip action=%s for msg=%s' % ( action, cmd)
                    logger.error(msg)

        if regConn in socks:
            msg = regConn.recv()
            regConn.send('Ok')
            print 'registered[sink] = ', msg

        if cmdConn in socks:
            pass
    # app.Boo()

if __name__ == '__main__':
    '''
    -T turf
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    args    = parser.parse_args()
    tweaks  = {
        'run_turf'  : args.turf,
        'run_domain': 'echo_sink',
    }
    logger.debug( 'execsinkapp: turf=%s', args.turf)
    with twkcx.Tweaks( **tweaks ):
        run_execSink()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\execsinkapp.py --turf=dev
'''