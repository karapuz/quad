'''
AUTHOR      : ilya presman, 2016
TYPE:       : example
DESCRIPTION : zmq.example module
'''

#
# Synchronized publisher
#

import zmq
# We wait for 10 subscribers
SUBSCRIBERS_EXPECTED = 1

def main():
    context = zmq.Context()
    # Socket to talk to clients
    publisher = context.socket(zmq.PUB)
    # set SNDHWM, so we don't drop messages for slow subscribers
    publisher.sndhwm = 1100000
    publisher.bind('tcp://*:5561')

    # Socket to receive signals
    syncservice = context.socket(zmq.REP)
    syncservice.bind('tcp://*:5562')

    # Get synchronization from subscribers
    subscribers = 0
    while subscribers < SUBSCRIBERS_EXPECTED:
        # wait for synchronization request
        msg = syncservice.recv()
        # send synchronization reply
        syncservice.send(b'')
        subscribers += 1
        print("+1 subscriber (%i/%i)" % (subscribers, SUBSCRIBERS_EXPECTED))

    # Now broadcast exactly 1M updates followed by END
    for i in range(10):
        publisher.send(b'Rhubarb')

    publisher.send(b'END')

if __name__ == '__main__':
    main()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\zmq\example213_poll\syncpub.py
'''