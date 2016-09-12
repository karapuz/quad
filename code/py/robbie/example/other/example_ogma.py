from   robbie.util.logging import logger
import robbie.example.other.ogma as ogma

def run1():
    ogmadb = ogma.Ogma(dirName=r'c:\temp\ogma1', coreName='db-dict1', options=[ogma.FLUSH_SESSION] )
    N = 10
    zs = []
    for x in xrange(N):
        z = {'a':x, 'b':x+1}
        zs.append(z)
    logger.debug('session-flush start N=%d', N,)
    for z in zs:
        ogmadb.write(z)
    ogmadb.flush()
    logger.debug('end')

    ogmadb = ogma.Ogma(dirName=r'c:\temp\ogma1', coreName='db-dict1', mode='read' )
    zs1 = []
    for z in ogmadb:
        zs1.append(z)
    logger.debug('end')
    print zs1
    print zs
    assert zs1 == zs

if __name__ == '__main__':
    run1()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\other\example_ogma.py
'''
