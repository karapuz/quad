from   robbie.util.logging import logger
import robbie.example.other.ogma as ogma

def run1():
    ogmadb = ogma.Ogma(dirName=r'c:\temp\ogma1', coreName='db-numpy', mode='read' )
    logger.debug('start')
    cont = True
    while cont:
        cont, val = ogmadb.read()
        if not cont:
            break
        #print val

    ogmadb.flush()
    logger.debug('end')

def run2():
    dirName     = r'c:\temp\ogma1'
    coreName    = 'db-small'

    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION] )
    N = 10
    z = {'a':1, 'b':2}
    for i in xrange(N):
        ogmadb.write(z)
    ogmadb.flush()

    logger.debug('start')
    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='read' )
    for x in ogmadb:
        print x
    logger.debug('end')

def run3():
    dirName     = r'c:\temp\ogma1'
    coreName    = 'db-small'

    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='write' )
    N = 10
    z = {'a':1, 'b':2}
    for i in xrange(N):
        ogmadb.write(z)
    ogmadb.flush()

    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='append' )
    N = 10
    z = {'a':2, 'b':3}
    for i in xrange(N):
        ogmadb.write(z)
    ogmadb.flush()

    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='append' )
    N = 10
    z = {'a':4, 'b':5}
    for i in xrange(N):
        ogmadb.write(z)
    ogmadb.flush()

    logger.debug('start')
    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='read' )
    for x in ogmadb:
        print x
    logger.debug('end')

if __name__ == '__main__':
    run3()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\other\example_ogmaread.py
'''