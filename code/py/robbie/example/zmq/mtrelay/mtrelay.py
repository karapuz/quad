"""

   Multithreaded relay

   Author: Guillaume Aubert (gaubert) <guillaume(dot)aubert(at)gmail(dot)com>

"""

import threading
import zmq

def step1(context=None):
    """Step 1"""
    context = context or zmq.Context.instance()
    # Signal downstream to step 2
    sender = context.socket(zmq.PAIR)
    sender.connect("tcp://localhost:5001")

    sender.send(b"")

def step2(context=None):
    """Step 2"""
    context = context or zmq.Context.instance()
    # Bind to inproc: endpoint, then start upstream thread
    receiver = context.socket(zmq.PAIR)
    receiver.bind("tcp://*:5001")

    thread = threading.Thread(target=step1)
    thread.start()

    # Wait for signal
    msg = receiver.recv()

    # Signal downstream to step 3
    sender = context.socket(zmq.PAIR)
    sender.connect("tcp://localhost:5000")
    sender.send(b"")

def main():
    """ server routine """
    # Prepare our context and sockets
    context = zmq.Context.instance()

    # Bind to inproc: endpoint, then start upstream thread
    receiver = context.socket(zmq.PAIR)
    receiver.bind("tcp://*:5000")

    thread = threading.Thread(target=step2)
    thread.start()

    # Wait for signal
    string = receiver.recv()

    print("Test successful!")

    receiver.close()
    context.term()

if __name__ == "__main__":
    main()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\zmq\mtrelay\mtrelay.py
'''