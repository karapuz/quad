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
    return now.strftime('SRC_%Y%m%d_%H%M%S')

def toVal(k,v):
    return str(v)

def toStr(c):
    nc = {}
    for k,v in c.iteritems():
        nc[str(k)] = toVal(k,v)
    return nc

def run_execsrc():
    # prepare fix
    # Prepare our context and sockets
    context     = zmq.Context()
    turf        = twkval.getenv('run_turf')
    agt_comms   = turfutil.get(turf=turf, component='communication')
    agt_list    = turfutil.get(turf=turf, component='agents')

    cmd_port    = agt_comms['SRCCMD']['port_cmd']
    cmdConn     = context.socket(zmq.REP)
    cmdConn.bind("tcp://*:%s" % cmd_port)

    conns   = {}
    sigs    = []
    for agent, agt_comm in agt_comms.iteritems():
        if agent not in agt_list:
            logger.debug('not an agent: %s', agent)
            continue
        logger.debug( 'execsrc: agent=%s', agent)
        port_execSrc    = agt_comm['agent_execSrc']
        port_sigCon     = agt_comm['agent_sigCon']

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port_execSrc)
        conns[agent] = c

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port_sigCon)
        sigs.append( c )

    signalStrat = echocore.SignalStrat(conns)
    msgAdapter  = messageadapt.Message(['ECHO1','ECHO1'], 'TIME')
    appThread, thread = execsrclink.init(
                            tweakName   = 'fix_SrcConnConfig',
                            signalStrat = signalStrat,
                            msgAdapter  = msgAdapter)
    app         = appThread.getApplication()

    while 1:
        msgs    = cmdConn.recv()
        msg     = json.loads(msgs)
        msg     = toStr(msg)
        cmd     = msg['cmd']
        agent   = msg['agent']
        print 'got', msg

        cmdConn.send('done')
        if cmd == 'KILL':
            for c in sigs:
                c.send( cmd ) # process task
            time.sleep(10)
            break
        elif cmd == 'SEND':
            app.sendOrder(
                senderCompID = 'BANZAI',
                targetCompID = 'FIXIMULATOR',
                account      = agent,
                orderId      = newOrderId(),
                symbol       = 'IBM',
                qty          = 1000,
                price        = 200,
                timeInForce  = fut.Val_TimeInForce_DAY,
                tagVal       = None )
        else:
            logger.error('Unknown cmd=%s', cmd)

if __name__ == '__main__':
    '''
    -T turf
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    args    = parser.parse_args()
    tweaks  = {
        'run_turf'  : args.turf,
        'run_domain': 'echo_source',
    }
    logger.debug( 'agent: turf=%s', args.turf)
    with twkcx.Tweaks( **tweaks ):
        run_execsrc()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\execsrcapp.py --turf=dev
'''