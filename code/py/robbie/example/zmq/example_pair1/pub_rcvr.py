"""
Multithreaded Hello World server
Author: Guillaume Aubert (gaubert) <guillaume(dot)aubert(at)gmail(dot)com>
"""
import zmq


def main():
    """Server routine"""
    url_client = "tcp://localhost:5555"
    # Prepare our context and sockets
    context = zmq.Context.instance()
    # Socket to talk to clients
    socket  = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, b'')
    socket.connect(url_client)

    for x in xrange(10):
        string = socket.recv()
        print("Received request: [ %s ]" % (string))

if __name__ == "__main__":
    main()
