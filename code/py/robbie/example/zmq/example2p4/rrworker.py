import zmq
import signal

context = zmq.Context()
port    = 5560
socket  = context.socket(zmq.REP)
socket.bind("tcp://*:%s" % port)

def signal_handler(signum, frame):
     print("W: custom interrupt handler called.")

signal.signal(signal.SIGINT, signal_handler)

while True:
    message = socket.recv()
    print("Received request: %s" % message)
    socket.send(b"World")

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\zmq\example2p4\rrworker.py
'''