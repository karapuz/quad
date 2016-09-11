from   robbie.util.logging import logger
import robbie.example.other.ogma as ogma

def run():
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

if __name__ == '__main__':
    run()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\python27\python.exe robbie\example\other\example_ogmaread.py
'''