import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.util.filelogging as filelogging

def run():
    tweaks = {'env_loggerDir':r'c:\temp\20160813'}
    with twkcx.Tweaks(**tweaks):
        logger.debug('start')
        flogger = filelogging.FileLogger(name='test1', attrs=('a','b','c'), flush=True)

        for x in xrange(100000):
            flogger.debug(label='A',args={'a':1+x, 'b': 2+x, 'c': 3+float(x)/1000})

        logger.debug('finish')

if __name__ == '__main__':
    run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\logging\logger.py
'''