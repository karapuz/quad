import time
import zmq


def main():
    """ server routine """
    # Prepare our context and sockets
    context = zmq.Context.instance()
    # Signal downstream to step 2
    sender = context.socket(zmq.PUB)
    sender.bind('tcp://*:5555')

    time.sleep(10)
    for x in xrange(10):
        sender.send(b"THis is a message %d" % x)
    print 'done'

if __name__ == "__main__":
    main()
