'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.agent module
'''

import zmq
import json
import argparse
import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger

def run_cmd(cmd, agent, data):
    # Prepare our context and sockets
    turf        = twkval.getenv('run_turf')
    context     = zmq.Context()

    rediPort    = turfutil.get(turf=turf, component='communication', sub='REDI')['port_cmd']
    rediCmd     = context.socket(zmq.PAIR)
    rediCmd.connect ("tcp://localhost:%s" % rediPort)

    if cmd == 'REDI':
        d     = {'cmd': cmd}
        d.update(eval(data))
        msg     = json.dumps( d )
        for x in ('action', 'qty', 'symbol', 'price', 'orderId', 'qty'):
            assert x in d
        logger.debug("REDI: Sending %s [%s]" % (rediPort, msg))
        rediCmd.send(msg)
        msg = rediCmd.recv()
        logger.debug("REDI: Received reply %s [%s]" % (rediPort, msg))

if __name__ == '__main__':
    '''
    -T turf
    -C cmd
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-C", "--cmd", help="command",     action="store")
    parser.add_argument("-A", "--agent", help="agent",     action="store")
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    parser.add_argument("-D", "--data",  help="data",      action="store")
    args    = parser.parse_args()
    tweaks  = {
        'run_turf'  : args.turf,
    }
    logger.debug( 'agent: turf=%s cmd=%s', args.turf, args.cmd)
    with twkcx.Tweaks( **tweaks ):
        run_cmd(args.cmd, args.agent, args.data)

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=REDI --turf=dev --data="{'action':'ORDER_TYPE_NEW','orderType':'ORDER_TYPE_NEW','signalName':'ECHO1','execTime':'NOW','orderId':'ORDER_CMD_1','symbol':'IBM','qty':'100','price':100}"

'''