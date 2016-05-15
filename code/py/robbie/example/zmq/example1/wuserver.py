__author__ = 'ilya'

# Example 1-7. Weather update server (wuserver.py)
# Weather update server
# Binds PUB socket to tcp://*:5556
# Publishes random weather updates
#

import zmq
import time
from random import randrange
from robbie.util.logging import logger

logger.debug('loaded libs')
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")

time.sleep(5)

logger.debug('connected sockets')
#while True:
for i in xrange(1000000):
    zipcode = randrange(1, 100000)
    temperature = randrange(-80, 135)
    relhumidity = randrange(10, 60)
    socket.send_string("%i %i %i" % (zipcode, temperature, relhumidity))
logger.debug('done publishing')
