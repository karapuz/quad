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
from   robbie.echo.stratutil import EXECUTION_MODE

import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.execution.util as executil
import robbie.execution.execsrclink as execsrclink
import robbie.execution.messageadapt as messageadapt

def run_execSink():
    context     = zmq.Context()
    turf        = twkval.getenv('run_turf')
    agt_comms   = turfutil.get(turf=turf, component='communication')
    agt_list    = turfutil.get(turf=turf, component='agents')
    signalMode  = turfutil.get(turf=turf, component='signal')

    poller      = zmq.Poller()

    reg_port    = agt_comms['SNK_REG']['port_reg']
    regConn     = context.socket(zmq.REP)
    regConn.bind("tcp://*:%s" % reg_port)
    poller.register(regConn, zmq.POLLIN)

    cmd_port    = agt_comms['SNK_CMD']['port_cmd']
    cmdConn     = context.socket(zmq.REP)
    cmdConn.bind("tcp://*:%s" % cmd_port)
    poller.register(cmdConn, zmq.POLLIN)

    agentIn     = {}
    agentOut    = {}

    for agent, agt_comm in agt_comms.iteritems():
        if agent not in agt_list:
            logger.debug('EXECSINKAPP: not an agent: %s', agent)
            continue
        logger.debug( 'EXECSINKAPP: agent=%s', agent)

        agent_execSnkIn  = agt_comm['agent_execSnkIn']
        agent_execSnkOut = agt_comm['agent_execSnkOut']

        agentSinkIntCon = context.socket(zmq.PAIR) # PUB
        agentSinkIntCon.bind('tcp://*:%s' % agent_execSnkIn)

        agentSinkOutCon = context.socket(zmq.PAIR) # SUB
        agentSinkOutCon.connect('tcp://localhost:%s' % agent_execSnkOut)

        poller.register(agentSinkOutCon, zmq.POLLIN)
        agentIn [ agent ] = agentSinkIntCon
        agentOut[ agent ] = agentSinkOutCon

    signalStrat = echocore.SignalStrat(agentIn, mode=signalMode)
    msgAdapter  = messageadapt.Message(['ECHO1','ECHO1'], 'TIME')
    tweakName   = 'fix_SinkConnConfig'
    appThread, thread = execsrclink.init(
                            tweakName   = tweakName,
                            signalStrat = signalStrat,
                            mode        = signalMode,
                            msgAdapter  = msgAdapter)

    app          = appThread.getApplication()
    commCreds    = twkval.getenv( tweakName )
    senderCompID = commCreds[ 'sender' ]
    targetCompID = commCreds[ 'target' ]

    # Process messages from both sockets
    while True:
        logger.debug('EXECSINKAPP: in the loop')
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        for agent, c in agentOut.iteritems():
            if c in socks:
                cmds        = c.recv() # process signal
                cmd         = json.loads(cmds)
                action      = cmd['action']
                data        = cmd['data']
                data        = executil.toStr(data)

                logger.debug('EXECSINKAPP: AGNTOUT action = %s data = %s', action, data)
                sinkproc.signal2order(
                    app          = app,
                    action       = action,
                    data         = data,
                    senderCompID = senderCompID,
                    targetCompID = targetCompID )

        if regConn in socks:
            msg = regConn.recv()
            regConn.send('OK')
            logger.debug('EXECSINKAPP: REGISTERED[SINK] = %s', msg)

        if cmdConn in socks:
            msgs    = cmdConn.recv()
            msg     = json.loads(msgs)
            msg     = executil.toStr(msg)
            action     = msg['cmd']
            logger.debug('EXECSINKAPP: CMD=%s', msg)
            cmdConn.send('RECEIVED')

            if action == 'KILL':
                time.sleep(10)
                break
            else:
                logger.error('EXECSINKAPP: Unknown action=%s', action)

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
    logger.debug( 'EXECSINKAPP: turf=%s', args.turf)
    with twkcx.Tweaks( **tweaks ):
        run_execSink()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\execsinkapp.py --turf=dev
'''
