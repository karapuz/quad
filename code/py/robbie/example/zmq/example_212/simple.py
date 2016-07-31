import zmq
import threading

def sendTimedSignal(msg):
    context = zmq.Context.instance()
    sender = context.socket(zmq.PAIR)
    sender.connect("inproc://timer")
    sender.send(str(msg))

def main():
    context = zmq.Context.instance()
    receiver = context.socket(zmq.PAIR)
    receiver.bind("inproc://timer")

    threading.Timer(5, sendTimedSignal, ("5.0",)).start()
    threading.Timer(5.01, sendTimedSignal, ("5.1",)).start()
    threading.Timer(10, sendTimedSignal, ("10.0",)).start()
    threading.Timer(11, sendTimedSignal, ("EXIT",)).start()

    poller = zmq.Poller()
    poller.register(receiver, zmq.POLLIN)

    print 'before while'
    while True:
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if receiver in socks:
            msg = receiver.recv()
            print '->', msg
            if msg == 'EXIT':
                break


    print("Test successful!")
    receiver.close()
    context.term()

if __name__ == "__main__":
    main()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\zmq\example_212\simple.py
'''