'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.execsnk module
'''

import zmq
import time

def run(ports):
    # Prepare our context and sockets
    context = zmq.Context()
    # Connect to task ventilator
    conns   = []
    sigs    = []
    for port in ports:
        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port)
        conns.append( c )

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % (port+1))
        sigs.append( c )

    # Process messages from both sockets
    for ix in xrange(1000):
        for c in conns:
            msg = '%d' % ix
            c.send( msg ) # process task
            print 'sending msg =', msg
    time.sleep(10)
    for c in sigs:
        c.send( '%d' % ix ) # process task

if __name__ == '__main__':
    run( [5555,])

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\agent.py --turf=dev
'''