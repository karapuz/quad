'''
AUTHOR      : ilya presman, 2016
TYPE:       : example
DESCRIPTION : zmq.example module
'''

#
# Synchronized publisher
#

import zmq

def main():
    context = zmq.Context()
    # Socket to talk to clients
    publisher = context.socket(zmq.PUB)
    # set SNDHWM, so we don't drop messages for slow subscribers
    # publisher.sndhwm = 1100000
    publisher.bind('tcp://*:5561')

    # Socket to receive signals
    for i in range(100000):
        print 'sending %s' % i
        publisher.send(b'Rhubarb')

    publisher.send(b'END')

    import time
    while 1:
        time.sleep(1)

if __name__ == '__main__':
    main()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\zmq\example_pubsub\syncpub.py
'''