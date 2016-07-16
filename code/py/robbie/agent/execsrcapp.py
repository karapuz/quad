'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.execsrc module
'''

import zmq
import json
import time
import argparse
import robbie.fix.util as fut
import robbie.echo.core as echocore
import robbie.echo.stratutil as stratutil

import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.execution.util as executil
import robbie.execution.execsrclink as execsrclink
import robbie.execution.messageadapt as messageadapt

def run_execsrc():
    # prepare fix
    # Prepare our context and sockets
    context     = zmq.Context()
    turf        = twkval.getenv('run_turf')
    agt_comms   = turfutil.get(turf=turf, component='communication')
    agt_list    = turfutil.get(turf=turf, component='agents')

    signalMode  = turfutil.get(turf=turf, component='signal')

    poller      = zmq.Poller()

    cmd_port    = agt_comms['SRC_CMD']['port_cmd']
    cmdConn     = context.socket(zmq.REP)
    cmdConn.bind("tcp://*:%s" % cmd_port)
    poller.register(cmdConn, zmq.POLLIN)

    reg_port    = agt_comms['SRC_REG']['port_reg']
    regConn     = context.socket(zmq.REP)
    regConn.bind("tcp://*:%s" % reg_port)
    poller.register(regConn, zmq.POLLIN)

    conns   = {}
    sigs    = []
    for agent, agt_comm in agt_comms.iteritems():
        if agent not in agt_list:
            logger.debug('EXECSRCAPP: not an agent: %s', agent)
            continue
        logger.debug( 'EXECSRCAPP: Agent=%s', agent)
        port_execSrc    = agt_comm['agent_execSrc']
        port_sigCon     = agt_comm['agent_sigCon']

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port_execSrc)
        conns[agent] = c

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port_sigCon)
        sigs.append( c )

    signalStrat = echocore.SignalStrat(conns,mode=signalMode)
    msgAdapter  = messageadapt.Message(['ECHO1','ECHO1'], 'TIME')
    appShell, _ = execsrclink.init(
                    tweakName   = 'fix_SrcConnConfig',
                    signalStrat = signalStrat,
                    mode        = signalMode,
                    msgAdapter  = msgAdapter)
    app         = appShell.getApplication()

    while True:
        logger.debug('in the loop')
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if regConn in socks:
            msg = regConn.recv()
            regConn.send('OK')
            logger.debug('EXECSRCAPP: REGISTERED[SRC] = %s', msg)
            continue

        if cmdConn in socks:
            msgs    = cmdConn.recv()
            msg     = json.loads(msgs)
            msg     = executil.toStr(msg)
            cmd     = msg['cmd']
            logger.debug('EXECSRCAPP: CMD=%s', msg)
            cmdConn.send('RECEIVED')

            if cmd == 'KILL':
                for c in sigs:
                    c.send( cmd ) # process task
                time.sleep(10)
                break

            elif cmd == 'SEND':
                agent   = msg['agent']
                qty     = int(msg.get('qty','1000'))
                symbol  = msg.get('sybol', 'IBM')
                app.sendOrder(
                    senderCompID = 'BANZAI',
                    targetCompID = 'FIXIMULATOR',
                    account      = agent,
                    orderId      = stratutil.newOrderId('SRC'),
                    symbol       = symbol,
                    qty          = qty,
                    price        = 200,
                    timeInForce  = fut.Val_TimeInForce_DAY,
                    tagVal       = None )

            elif cmd == 'CX':
                agent         = msg['agent']
                origOrderId   = msg['origOrderId']
                if 'qty' in msg:
                    qty = int(msg['qty'])
                else:
                    qty = None
                symbol        = msg.get('sybol', 'IBM')
                app.cancelOrder(
                    senderCompID = 'BANZAI',
                    targetCompID = 'FIXIMULATOR',
                    account      = agent,
                    orderId      = stratutil.newOrderId('CX_SRC'),
                    symbol       = symbol,
                    qty          = qty,
                    origOrderId  = origOrderId)

            else:
                logger.error('EXECSRCAPP: Unknown cmd=%s', cmd)

            continue

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

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\execsrcapp.py --turf=dev_full
'''
