'''
AUTHOR      : ilya presman, 2016
TYPE:       : example
DESCRIPTION : zmq.example module
'''

#
# Synchronized subscriber
#

import time
import zmq

def main():
    context = zmq.Context()

    # First, connect our subscriber socket
    subscriber = context.socket(zmq.PAIR)
    subscriber.connect('tcp://localhost:5561')
    # subscriber.setsockopt(zmq.SUBSCRIBE, b'')
    # time.sleep(1)
    poller      = zmq.Poller()
    poller.register(subscriber, zmq.POLLIN)

    # Second, synchronize with publisher
    syncclient = context.socket(zmq.REQ)
    syncclient.connect('tcp://localhost:5562')
    # send a synchronization request
    syncclient.send(b'')
    # wait for synchronization reply
    syncclient.recv()
    # Third, get our updates and report how many we got
    nbr = 0
    while True:
        print 'in the loop'
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if subscriber in socks:
            msg = subscriber.recv() # process signal
            if msg == b'END':
                break
            nbr += 1
    print ('Received %d updates' % nbr)

if __name__ == '__main__':
    main()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\zmq\example213_pairpoll\syncsub.py
'''
