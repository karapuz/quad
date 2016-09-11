from   robbie.util.logging import logger
import robbie.example.other.ogma as ogma

def run1():
    ogmadb = ogma.Ogma(dirName=r'c:\temp\ogma1', coreName='db' )
    logger.debug('start')
    for i in xrange(1000000):
        ogmadb.write({'a':1, 'b':2})
    ogmadb.flush()
    logger.debug('end')

    ogmadb = ogma.Ogma(dirName=r'c:\temp\ogma10', coreName='db-noflush', options=[objstream.FLUSH_SESSION] )
    logger.debug('start')
    for i in xrange(10):
        ogmadb.write({'a':1, 'b':2})
    ogmadb.flush()
    logger.debug('end')

import numpy
def run2():
    ogmadb = ogma.Ogma(dirName=r'c:\temp\ogma1', coreName='db-numpy1', options=[ogma.FLUSH_SESSION] )
    N = 1000000
    n = 5
    z = numpy.zeros(n)
    logger.debug('session-flush start N=%d n=%d', N, n)
    for i in xrange(N):
        ogmadb.write(z)
    ogmadb.flush()
    logger.debug('end')

    ogmadb = ogma.Ogma(dirName=r'c:\temp\ogma1', coreName='db-numpy2' )
    logger.debug('obj-flush start N=%d n=%d', N, n)
    for i in xrange(N):
        ogmadb.write(z)
    ogmadb.flush()
    logger.debug('end')

if __name__ == '__main__':
    run2()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\other\example_ogma.py
'''