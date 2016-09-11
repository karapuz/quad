import time
from   robbie.util.logging import logger, LoggingModes

def run():
    logger.debug('1')

    logger.setMode(mode=LoggingModes.FILE, data=r'c:\temp\zoo\a.txt')

    for x in xrange(1000000):
        logger.debug('-> %s',x)
        print x
        time.sleep(5)

if __name__ == '__main__':
    run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\logging\logger2.py
'''