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

    srcPort    = turfutil.get(turf=turf, component='communication', sub='SRC_CMD')['port_cmd']
    srcCmd      = context.socket(zmq.REQ)
    srcCmd.connect ("tcp://localhost:%s" % srcPort)

    snkPort    = turfutil.get(turf=turf, component='communication', sub='SNK_CMD')['port_cmd']
    snkCmd      = context.socket(zmq.REQ)
    snkCmd.connect ("tcp://localhost:%s" % snkPort)

    rediPort    = turfutil.get(turf=turf, component='communication', sub='REDI')['port_cmd']
    rediCmd     = context.socket(zmq.PAIR)
    rediCmd.connect ("tcp://localhost:%s" % rediPort)

    if cmd == 'SEND':
        d     = {'cmd': cmd}
        d.update(eval(data))
        for x in ('agent', 'action', 'qty', 'symbol', 'price', 'qty'):
            assert x in d
        msg     = json.dumps( d )
        logger.debug("CMD: Sending %s [%s]" % (srcPort, msg))
        srcCmd.send(msg)
        msg     = srcCmd.recv()
        logger.debug("CMD: Received reply %s [%s]" % (srcPort, msg))

    elif cmd == 'CX':
        d     = {'cmd': cmd, 'agent': agent}
        d.update(eval(data))
        msg     = json.dumps( d )
        assert 'origOrderId' in d
        assert 'qty' in d
        logger.debug("CMD: Sending %s [%s]" % (srcPort, msg))
        srcCmd.send(msg)
        msg = srcCmd.recv()
        logger.debug("CMD: Received reply %s [%s]" % (srcPort, msg))

    elif cmd == 'REDI':
        d     = {'cmd': cmd}
        d.update(eval(data))
        msg     = json.dumps( d )
        for x in ('action', 'qty', 'symbol', 'price', 'orderId', 'qty'):
            assert x in d
        logger.debug("REDI: Sending %s [%s]" % (rediPort, msg))
        rediCmd.send(msg)
        msg = rediCmd.recv()
        logger.debug("REDI: Received reply %s [%s]" % (rediPort, msg))

    elif cmd == 'KILL':
        if data is None:
            data = ('SRC', 'SNK')

        if 'SRC' in data:
            msgOut     = json.dumps( {'cmd': cmd } )
            logger.debug("CMD: SRC Sending %s [%s]" % (srcPort, msgOut))
            srcCmd.send(msgOut)
            msgIn = srcCmd.recv()
            logger.debug("CMD: SRC Received reply %s [%s]" % (srcPort, msgIn))

        if 'SNK' in data:
            logger.debug("CMD: SNK Sending %s [%s]" % (snkPort, msgOut))
            snkCmd.send(msgOut)
            msgIn = snkCmd.recv()
            logger.debug("CMD: SNK Received reply %s [%s]" % (snkPort, msgIn))
    else:
        logger.error('Uknown cmd=%s' % cmd )

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
del C:\Users\ilya\GenericDocs\dev\data\margot\20160718\fix\store\*.*
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=KILL --turf=dev --data="('SRC',)"

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=SEND --turf=dev_full --agent=ECHO1

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=CX --turf=dev --agent=ECHO1 --data="{'origOrderId':'SRC_20160714_205230_1','qty':'100'}"

c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=KILL --turf=ivp_redi_fix --data="('SRC','SNK')"

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=REDI --turf=dev --data="{'action':'ORDER_TYPE_NEW','orderType':'ORDER_TYPE_NEW','signalName':'ECHO1','execTime':'NOW','orderId':'ORDER_CMD_1','symbol':'IBM','qty':'100','price':100}"

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=SEND --turf=ivp_redi_fix --data="{'action':'ORDER_TYPE_NEW','orderType':'ORDER_TYPE_NEW','qty':'-100','agent':'ECHO1','execTime':'NOW','symbol':'IBM','price':100}"
c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=SEND --turf=ivp_redi_fix --data="{'action':'ORDER_TYPE_NEW','orderType':'ORDER_TYPE_NEW','qty':'100','agent':'ECHO1','execTime':'NOW','symbol':'IBM','price':100}"

    'OrderType' : {
        '1': 'Market',
        '2': 'Limit',
        '3': 'Stop',
        '4': 'StopLimit',
        '5': 'MarketOnClose',
        '6': 'WithOrWithout',
        '7': 'LimitOrBetter',
        '8': 'LimitWithOrWithout',
        '9': 'OnBasis',
        'A': 'OnClose',
        'B': 'LimitOnClose',
        'C': 'ForexMarket',
        'D': 'PreviouslyQuoted',
        'E': 'PreviouslyIndicated',
        'F': 'ForexLimit',
        'G': 'ForexSwap',
        'H': 'ForexPreviouslyQuoted',
        'I': 'Funari',
        'P': 'Pegged',

'''