'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : execution.util - utils for the exec
'''
import robbie.fix.util as fut
from   robbie.util.logging import logger

def testAdapter(stratsNamess, timeNames):
    h  = []
    ix = [0]
    def _ma(message, callName):
        ix[0] = (ix[0] % len(stratsNamess))
        ix[0] += 1
        return ix[0]
    return _ma

class Message(object):
    def __init__(self, stratsNamess, timeNames):
        self._stratsNamess = stratsNamess
        self._timeNames    = timeNames
        self._ix           = 0
        self._history      = []
        self._debug        = False
        if self._debug:
            logger.debug('Message: self=%s', str(id(self)))

    def __call__(self, message, callName):
        self._message       = message
        self._orig_getField = message.getField
        message.getField    = self.getField
        if self._debug:
            logger.debug('Message: self=%s __call__', str(id(self)))
        return self

    def __enter__(self):
        if self._debug:
            logger.debug('Message: self=%s __enter__', str(id(self)))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._message.getField    = self._orig_getField
        if self._debug:
            logger.debug('Message: self=%s __exit__ ', str(id(self)))

    def getField(self, tag ):
        '''
            orderId     = message.getField( fut.Tag_ClientOrderId   )
        '''
        if tag == fut.Tag_TransactTime:
            return 'TIME'
        elif tag == fut.Tag_Account:
            return 'PRESMAN'
        else:
            try:
                return self._orig_getField(tag)
            except:
                logger.debug('getField tag=%s', tag)
                raise

class Communication(object):
    def __init__(self):
        pass

    def send( self, *argv):
        print 'send->', argv

'''
import robbie.execution.messageadapt as messageadapt
reload( messageadapt )
ma = messageadapt.testAdapter(stratsNamess=[1,2,3], timeNames=None)
ma(1,2)

'''