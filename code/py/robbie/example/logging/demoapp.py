import time
import argparse
from   robbie.util.logging import logger, LoggingModes

def run():
    for ix,e in enumerate( xrange(1000000)):
        logger.debug( '%s, %s, %s', ix, e, 'x' * 1000)
        time.sleep(1)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    parser.add_argument("-L", "--logpath",  help="log path", action="store")
    args    = parser.parse_args()

    if args.logpath:
        logger.debug('switching to file logger path=%s', args.logpath)
        logger.setMode(mode=LoggingModes.FILE, data=args.logpath)
    run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\logging\demoapp.py --logpath=c:\temp\demoapp.log
'''