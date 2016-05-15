'''
'''
_allModes = [ 'sim', 'sim-seed', 'sim-prod', 'dev', 'trade-prod' ]

_modes = {
    'should-run-in-trade-block'     : 
                        set( [ 'dev', 'sim', 'sim-prod', 'trade-prod' ] ),
                        
    'should-run-in-update-block'     : 
                        set( [ 'dev', 'sim', 'sim-prod', 'trade-prod' ] ),

    'should-run-in-mrk2mrkt-block'     : 
                        set( [ 'dev', 'sim', 'sim-prod', 'trade-prod' ] ),
                        
    'should-run-in-calib-block'   : 
                        set( [ 'dev', 'sim', 'sim-seed', ] ),

    'needs-cache'   : 
                        set( [ 'sim', 'sim-seed', 'sim-prod', 'trade-prod'] ),
                        
    'needs-incr-special-processing'   : 
                        set( [ 'sim-seed' ] ),
}

def needsCache( mode ):
    return mode in _modes[ 'needs-cache' ]

def needsIncrSpecialProc( mode ):
    return mode in _modes[ 'needs-incr-special-processing' ]

def allModes():
    return _allModes

def isValidMode( mode ):
    return mode in _allModes

def modeRunsInUpdateBlock( mode ):
    ''' some modes should not be running in Update block '''    
    return mode in _modes[ 'should-run-in-update-block' ]

def modeRunsInCalibBlock( mode ):
    ''' some modes should not be running in Calib block '''    
    return mode in _modes[ 'should-run-in-calib-block' ]

def modeRunsInTradeBlock( mode ):
    ''' some modes should not be running in Trade block '''    
    return mode in _modes[ 'should-run-in-trade-block' ]

def modeRunsInMrk2MktBlock( mode ):
    ''' some modes should not be running in Mrk2Mkt block '''    
    return mode in _modes[ 'should-run-in-mrk2mrkt-block' ] 
