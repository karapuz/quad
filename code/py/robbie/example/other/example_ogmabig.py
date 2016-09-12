from   robbie.util.logging import logger
import robbie.example.other.ogma as ogma

def run3():
    dirName     = r'c:\temp\ogma1'
    coreName    = 'db-big'

    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='write' )
    N = 1000000
    z = {'a':1, 'b':2}
    logger.debug('small write start N=%d', N,)
    for i in xrange(N):
        ogmadb.write(z)
    ogmadb.flush()
    logger.debug('small write end')

    logger.debug('small read start N=%d', N,)
    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='read' )
    i = 0
    for x in ogmadb:
        i += 1
    logger.debug('small end, i=%d', i)

def run1():
    dirName     = r'c:\temp\ogma1'
    coreName    = 'db-big-1000-ints'

    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='write' )
    N = 100000
    z = [1] * 1000
    logger.debug('(1000 ints) write start N=%d', N,)
    for i in xrange(N):
        ogmadb.write(z)
    ogmadb.flush()
    logger.debug('(1000 ints) end')

    logger.debug('(1000 ints) read start N=%d', N,)
    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='read' )
    i = 0
    for x in ogmadb:
        i += 1
    logger.debug('(1000 ints) end, i=%d', i)

def run2():
    dirName     = r'c:\temp\ogma1'
    coreName    = 'db-big-objstream'

    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='write' )
    N = 100000
    obj = dict( ( 'x_%d'% i, 'STRING_%i' % i ) for i in xrange(200) )
    z = {'specs':('ERROR', 'BAD_FACILITY_TYPE', '01'), 'obj': obj}
    logger.debug('objstream write start N=%d', N,)
    for i in xrange(N):
        ogmadb.write(z)
    ogmadb.flush()
    logger.debug('objstream write end')

    logger.debug('objstream read start N=%d', N,)
    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='read' )
    i = 0
    for x in ogmadb:
        i += 1
    logger.debug('objstream end, i=%d', i)

if __name__ == '__main__':
    run1()
    run2()
    run3()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\other\example_ogmabig.py
'''