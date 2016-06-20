'''
AUTHOR      : ilya presman, 2016
TYPE:       : example
DESCRIPTION : zmq.example module
'''

#
# Synchronized subscriber
#

import zmq

def main():
    context = zmq.Context()

    subscriber = context.socket(zmq.SUB)
    subscriber.connect('tcp://localhost:5561')
    subscriber.setsockopt(zmq.SUBSCRIBE, b'')

    while True:
        msg = subscriber.recv()
        if msg == b'END':
            break
        print ('Received msg = %s' % msg)

if __name__ == '__main__':
    main()


'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\zmq\example_pubsub\syncsub.py
'''