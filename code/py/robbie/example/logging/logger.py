import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.util.filelogging as filelogging

def run2():
    logger = filelogging.getFileLogger(domain='this_domain', user='this_user', session='this_session', name='this_name', attrs=('a','b','c','d'))
    logger.debug('THIS', {'a':1, 'b':2, 'c':3, 'd':4 })

if __name__ == '__main__':
    run2()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\logging\logger.py
'''