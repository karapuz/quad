from   robbie.util.logging import logger
import robbie.example.other.ogma as ogma

def run1():
    dirName     = r'c:\temp\ogma1'
    coreName    = 'db-big-1000-ints'
    N = 10000

    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='write' )
    z = [1] * 1000
    logger.debug('write start 1000ints N=%d', N,)
    for i in xrange(N):
        ogmadb.write(z)
    ogmadb.flush()
    logger.debug('end')

    i = 0
    logger.debug('read start')
    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='read' )
    for x in ogmadb:
        i += 1
    logger.debug('read end')

    Nn = 100
    ogmadb = ogma.Ogma(dirName=dirName, coreName=coreName, options=[ogma.FLUSH_SESSION], mode='read' )
    i = 0
    cont = True
    logger.debug('readmany start N=%d Nn=%d', N, Nn)
    while cont:
        cont, objs = ogmadb.readmany(Nn)
        if not cont:
            break
    logger.debug('end')
    ogmadb.flush()

if __name__ == '__main__':
    run1()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\other\example_ogmaread.py
'''