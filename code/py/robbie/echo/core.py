'''
TYPE    : lib
OWNER   : ilya
'''

class ExecutionStrategy(object):
    def __init__(self):
        pass

class EchoStrategy(object):
    def __init__(self, trader, execStrat):
        self._trader    = trader
        self._execStrat = execStrat

