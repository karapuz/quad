'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : execution.util - utils for the exec
'''
import robbie.fix.util as fut

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

    def __call__(self, message, callName):
        self._message       = message
        self._orig_getField = message.getField
        message.getField    = self.getField

    def getField(self, tag ):
        '''
            orderId     = message.getField( fut.Tag_ClientOrderId   )
        '''
        if tag == fut.Tag_TransactTime:
            return 'TIME'
        elif fut.Tag_Account:
            return 'PRESMAN'
        else:
            return self._orig_getField(tag)

class Communication(object):
    def __init__(self):
        pass

    def send( self, **argv):
        print 'send->', argv

'''
import robbie.execution.messageadapt as messageadapt
reload( messageadapt )
ma = messageadapt.testAdapter(stratsNamess=[1,2,3], timeNames=None)
ma(1,2)

'''