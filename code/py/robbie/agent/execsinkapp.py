'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.execsrc module
'''

import zmq
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

def newOrderId():
    now = datetime.datetime.now()
    return now.strftime('%Y%m%d_%H%M%S')

def run_execsrc():
    # prepare fix
    signalStrat = echocore.SignalStrat()
    appThread, thread = execsrclink.init(signalStrat=signalStrat,msgAdapter=None)
    app = appThread.getApplication()

    # Prepare our context and sockets
    context     = zmq.Context()
    turf        = twkval.getenv('run_turf')
    agt_comms   = turfutil.get(turf=turf, component='communication')
    agt_list    = turfutil.get(turf=turf, component='agents')

    cmd_port    = agt_comms['SRCCMD']['port_cmd']
    cmdConn     = context.socket(zmq.REP)
    cmdConn.bind("tcp://*:%s" % cmd_port)

    poller = zmq.Poller()

    subs   = {}
    pubs   = {}
    for agent, agt_comm in agt_comms.iteritems():
        if agent not in agt_list:
            logger.debug('not an agent: %s', agent)
            continue
        logger.debug( 'execsink: agent=%s', agent)

        port_execSnkIn  = agt_comm['port_execSnkIn']
        port_execSnkOut = agt_comm['port_execSnkOut']

        sinkInCon = context.socket(zmq.SUB)
        sinkInCon.setsockopt(zmq.SUBSCRIBE, b'')
        sinkInCon.connect('tcp://localhost:%s' % port_execSnkOut)
        subs[agent] = sinkInCon

        sinkOutCon = context.socket(zmq.PUB)
        sinkOutCon.bind('tcp://*:%s' % port_execSnkIn)
        pubs[agent] = sinkOutCon


        poller.register(sinkInCon,  zmq.POLLIN)

    cmd_port    = agt_comms['SRCCMD']['port_cmd']
    cmdConn     = context.socket(zmq.REP)
    cmdConn.bind("tcp://*:%s" % cmd_port)

    poller.register(cmdConn,  zmq.POLLIN)

    # Process messages from all sockets
    while True:
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        for agent, conn in subs.iteritems():

            if conn in socks:
                msg = conn.recv() # process task
                print 'got message = ', msg
                pubConn = pubs[agent]
                pubConn.send('This is the response!')
                print 'sent response message = ', msg

        if cmdMsg in socks:
            cmdMsg = cmdConn.recv()
            print 'CMD got', cmdMsg
            cmdConn.send('done')
            if cmdMsg == 'KILL':
                time.sleep(10)
                break

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
