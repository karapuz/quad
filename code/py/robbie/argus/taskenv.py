import Queue

class _Env( object ):
    def __init__(self):
        self._taskEnv     = {
            'marketData'        : {},
            'orderQueue'        : Queue.Queue(),
            'relations'         : None,
            'staticExposure'    : None,
            'initialExposure'   : None,
        }

_env = None

def init():
    global _env
    if _env == None:
        _env = _Env()
    return _env 

def objExists( category, name ):
    ''' '''
    _env = init()
    
    if category == 'env':
        return name in _env._taskEnv
    else:
        raise ValueError( 'Unknown %s %s' % ( category, name ) )

def delObj( category, name ):
    ''' '''
    _env = init()
    
    if category == 'env':
        del _env._taskEnv[ name ]
    else:
        raise ValueError( 'Unknown %s %s' % ( category, name ) )
    
def getObj( category, name ):
    ''' '''
    _env = init()
    
    if category == 'env':
        e = _env._taskEnv[ name ]
    else:
        raise ValueError( 'Unknown %s %s' % ( category, name ) )
    
    return e

def setObj( category, name, val ):
    ''' '''
    _env = init()
    
    if category == 'env':
        e = _env._taskEnv
        e[ name ] = val
    else:
        raise ValueError( 'Unknown %s %s' % ( category, name ) )
    