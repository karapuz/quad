'''
global repository
'''

import numpy

import meadow.lib.environment as environment

_strategies = {}
_params     = {}

def setStrategy( strategyName, cls, params ):
    global _strategies, _params
    
    if strategyName in _strategies:
        raise ValueError( 'Strategy name collision. Name %s exists!' % strategyName )
    
    _strategies[ strategyName ] = cls
    _params[ strategyName ] = params.copy()

    # True's
    for n0,n1 in [ ( 'Run', 'Slide' ) ]:
        if n1 in _params[ strategyName ][ n0 ]:
            continue
        _params[ strategyName ][ n0 ][ n1 ] = True

    # None's
    for n in ['CalibParams', 'TradeParams', 'SpecialProcessing' ]:
        if n in _params[ strategyName ]:
            continue
        _params[ strategyName ][ n ] = None

    _params[ strategyName ][ 'Run' ][ 'Step' ] = 1
    _params[ strategyName ][ 'StrategyName' ] = strategyName

def strategyExists( strategy, load=False ):
    ''' check if strategy exists '''
    if load:
        import meadow.strategy.repository as repo
        repo.init()
        
    global _strategies
    return strategy in _strategies
    
def getStrategy( endDate, strategyName ):
    ''' get strategy '''
    global _strategies, _params
    
    strategy    = _strategies[ strategyName ]
    params      = _params[ strategyName ]

    # these params are standard    
    params[ 'GetData' ][ 'TagName' ] = environment.formTagName( endDate )
    params[ 'GetData' ][ 'EndDate' ] = endDate

    return strategy, params

def getParams( strategyName ):
    ''' get strategy '''
    return _params[ strategyName ]

def initWithZeros( covMat ):
    return numpy.zeros( [covMat.shape[0], 1])

def clear():
    ''' clear strategy cache '''
    global _strategies, _params
    _strategies = {}
    _params     = {}

def show():
    ''' show all strategies '''
    global _strategies
    keys = sorted( _strategies.keys() )
    print 'Strategies'
    print '----------'
    for i,n in enumerate( keys ):        
        print '%3d %-20s' % (i, n)

def listNames():
    ''' list all strategy names '''
    global _strategies
    return sorted( _strategies.keys() )
