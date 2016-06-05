import zmq
# Prepare our context and sockets

context = zmq.Context()
port    = 5560
socket  = context.socket(zmq.REQ)
socket.connect ("tcp://localhost:%s" % port)

def signal_handler(signum, frame):
    print("W: custom interrupt handler called.")

for request in range(1,11):
    socket.send(b"Hello")
    message = socket.recv()
    print("Received reply %s [%s]" % (request, message))

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\zmq\example2p4\rrclient.py
'''
