import zmq
import itertools

def run(port):
    # Prepare our context and sockets
    context = zmq.Context()
    # Connect to task ventilator
    dataCon = context.socket(zmq.SUB)
    dataCon.setsockopt(zmq.SUBSCRIBE, b'')
    dataCon.connect('tcp://localhost:%s' % port)

    sigCon = context.socket(zmq.SUB)
    sigCon.setsockopt(zmq.SUBSCRIBE, b'')
    sigCon.connect('tcp://localhost:%s' % (port+1))

    # Initialize poll set
    poller = zmq.Poller()
    poller.register(dataCon, zmq.POLLIN)
    poller.register(sigCon,  zmq.POLLIN)

    # Process messages from both sockets
    while True:
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if dataCon in socks:
            msg = dataCon.recv() # process task
            print 'got message = ', msg
        if sigCon in socks:
            msg = sigCon.recv() # process weather update
            print 'got signal = ', msg
            break

if __name__ == '__main__':
    run( 5555 )
