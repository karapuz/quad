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
    appThread, thread = execsrclink.init()
    app = appThread.getApplication()
    print app

    # Prepare our context and sockets
    context     = zmq.Context()
    turf        = twkval.getenv('run_turf')
    agt_comms   = turfutil.get(turf=turf, component='communication')
    agt_list    = turfutil.get(turf=turf, component='agents')

    cmd_port    = agt_comms['SRCCMD']['port_cmd']
    cmdConn     = context.socket(zmq.REP)
    cmdConn.bind("tcp://*:%s" % cmd_port)

    conns   = []
    sigs    = []
    for agent, agt_comm in agt_comms.iteritems():
        if agent not in agt_list:
            logger.debug('not an agent: %s', agent)
            continue
        logger.debug( 'execsrc: agent=%s', agent)
        port_execSrc    = agt_comm['port_execSrc']
        port_sigCon     = agt_comm['port_sigCon']

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port_execSrc)
        conns.append( c )

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port_sigCon)
        sigs.append( c )

    # # Process messages from both sockets
    # for ix in xrange(1000):
    #     for c in conns:
    #         msg = '%d' % ix
    #         c.send( msg ) # process task
    #         print 'sending msg =', msg
    #
    # time.sleep(10)
    # for c in sigs:
    #     c.send( '%d' % ix ) # process task

    while 1:
        cmdMsg = cmdConn.recv()
        print 'got', cmdMsg
        cmdConn.send('done')
        if cmdMsg == 'KILL':
            for c in sigs:
                c.send( cmdMsg ) # process task
            time.sleep(10)
            break
        elif cmdMsg == 'SEND':
            app.sendOrder(
                senderCompID = 'BANZAI',
                targetCompID = 'FIXIMULATOR',
                orderId     = newOrderId(),
                symbol      = 'IBM',
                qty         = 1000,
                price       = 200,
                timeInForce = fut.Val_TimeInForce_DAY,
                tagVal      = None )
        else:
            logger.error('Unknown cmd=%s', cmdMsg)

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
