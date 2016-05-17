'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.core module
'''

class ExecutionStrategy(object):
    def __init__(self):
        pass

class EchoStrategy(object):
    def __init__(self, trader, execStrat):
        self._trader    = trader
        self._execStrat = execStrat

