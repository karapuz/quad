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

def run_cmd(cmd, agent):
    # Prepare our context and sockets
    turf            = twkval.getenv('run_turf')
    cmd_comms   = turfutil.get(turf=turf, component='communication', sub='SRCCMD')
    cmd_port    = cmd_comms['port_cmd']
    context     = zmq.Context()
    socket      = context.socket(zmq.REQ)
    socket.connect ("tcp://localhost:%s" % cmd_port)
    msg = json.dumps( {'cmd': cmd, 'agent': agent} )
    socket.send(msg)
    message = socket.recv()
    print("Received reply %s [%s]" % (cmd_port, message))


if __name__ == '__main__':
    '''
    -T turf
    -C cmd
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-C", "--cmd", help="command", action="store")
    parser.add_argument("-A", "--agent", help="agent", action="store")
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    args    = parser.parse_args()
    tweaks  = {
        'run_turf'  : args.turf,
    }
    logger.debug( 'agent: turf=%s cmd=%s', args.turf, args.cmd)
    with twkcx.Tweaks( **tweaks ):
        run_cmd(args.cmd, args.agent)

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=KILL --turf=dev

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=SEND --turf=dev --agent=ECHO1
c:\Python27\python2.7.exe robbie\agent\cmd.py --cmd=SEND --turf=dev --agent=ECHO2

'''