'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.mmap_array module
'''

import os
import time
import numpy
import robbie.util.margot as margot

from   robbie.util.logging import logger

#import meadow.lib.config as libconf
#import meadow.tweak.value as twkval
#import meadow.lib.space as libspace
import robbie.tweak.context as twkcx

'''
Structure
    /MargotRoot/Domain/Session/Activity

    MargotRoot   = /margot/ivp
    Domain       = echo         # pretty much a constant. Other domains: risk management?
    Session      = 20160504     # tied to a day
    Activity     = mirror       # is related to echo; mirror, trade, market
                    instrument_index
                        str:int { IBM: 1, MSFT: 2, ... }
                    instrument_exposure
                        float 1xN (N = 10,000)
                    order_new
                        float KxM (K=100, M = 500,000, K x M = 50MB)

    Activity    = trade
                    instrument_index
                        str:int { IBM: 1, MSFT: 2, ... }
                    instrument_exposure
                        float 1xN (N = 10,000)
                    order_new
                        float KxM (K=100, M = 500,000, K x M = 50MB)

    Activity    = market
                    book_top
                        float 3xN (N = 10,000) (bid, ask, qty)

'''
def _new( activity, shape, mode='w+', dtype='float32', initVals=None, domain=None, session=None  ):
    path = margot.getSessionSlice( domain=domain, session=session, activity=activity, create=True )
    arr  = numpy.memmap( path, dtype=dtype, mode=mode, shape=shape )
    
    if initVals != None:
        arr[:] = initVals
    return arr

def newWrite( activity, shape, dtype='float32', session=None, domain=None  ):
    return _new( domain=domain, session=session, activity=activity, shape=shape, mode='write', dtype=dtype )

def newRead( domain, session, activity, shape, dtype='float32' ):
    return _new( domain=domain, session=session, activity=activity, shape=shape, mode='r', dtype=dtype )

def new( domain, session, activity, shape, dtype='float32' ):
    return _new( domain=domain, session=session, activity=activity, shape=shape, mode='w+', dtype=dtype )

def zeros( domain, session, activity, shape, dtype='float32' ):
    return _new( domain=domain, session=session, activity=activity, shape=shape, mode='w+', dtype=dtype, initVals=0 )

def formVersionName( activity, suffix='version' ):
    ''' form version '''
    return '%s.%s' % ( activity, suffix )

def incrVersion( domain, session, activity ):
    ''' increment version '''
    
    shape   = (1, )
    dtype   = 'float32'

    activity = formVersionName( activity=activity )    
    
    version = newWrite( domain=domain, session=session, activity=activity, shape=shape, dtype=dtype )
    version[0]  = time.time()
    return version

def getVersion( domain, session, activity, create=False, debug=False ):
    ''' get version. -1 means there is no version yet '''
    
    shape   = (1, )
    dtype   = 'float32'
    activity = formVersionName( activity=activity )
    varPath = margot.getSharedVar( domain=domain, session=session, activity=activity, create=True )
    
    if debug:
        logger.debug( 'getVersion: varPath=%s' % varPath )
    
    if os.path.exists( varPath ):
        version = newRead( domain=domain, session=session, activity=activity, shape=shape, dtype=dtype )
    else:
        if create:
            version     = newWrite( domain=domain, session=session, activity=activity, shape=shape, dtype=dtype )
            version[0]  = time.time()
        else:
            version     = [-1]
            
    return version[0]

BbgVersion = 'bloomberg'
RelationVersion = 'relation'

def _varByTurf( typ='pathExists', component='relation', activity='relation-realized', isVersion=False, debug=True ):    
    turf    = twkval.getenv( 'run_turf' )
    domain  = libconf.get( turf=turf, component=component, sub='domain' )    
    tweaks  = {}
    if libconf.exists( turf=turf, component=component, sub='owner' ):
        owner   = libconf.get( turf=turf, component=component, sub='owner' )
        wnDir   = libconf.get( turf=turf, component='bob', sub='winstonRoot' )[ owner ]
        tweaks[ 'run_winstonRoot'] = wnDir

    session = libconf.get( turf=turf, component=component, sub='session' )
    if not session:
        logger.error( '_varByTurf: no session for typ=%s turf=%s component=%s activity=%s' % ( typ, turf, component, activity ) )
        return None
    
    if debug:
        logger.debug( '_varByTurf: typ=%s turf=%s session=%s component=%s activity=%s' % ( typ, turf, session, component, activity ) )
        
    with twkcx.Tweaks( ** tweaks ):
        if typ == 'pathExists':
            if isVersion:
                activity = formVersionName( activity )
            path = winston.getSharedVar( domain=domain, session=session, activity=activity, create=False )
            if debug:
                logger.debug( '_varByTurf: path=%s tweaks=%s' % ( path, str( tweaks ) ) )
                
            return os.path.exists( path )
        else:
            if isVersion:
                return getVersion( domain=domain, session=session, activity=activity, create=True, debug=debug )
            else:
                shape = ( libspace.MAX_SYMBOLS, )
                return newRead( domain=domain, session=session, activity=activity, shape=shape, dtype='float32' )

def getVersionByTurf( component, activity, debug=True ):
    return _varByTurf( typ='version', component=component, activity=activity, isVersion=True, debug=debug )

def checkSharedExistsByTurf( component, activity, debug=True ):
    return _varByTurf( typ='pathExists', component=component, activity=activity, isVersion=True, debug=debug )

def getVarByTurf( component, activity, debug=True ):
    return _varByTurf( typ='version', component=component, activity=activity, isVersion=False, debug=debug )

def checkSharedVarExistsByTurf( component, activity, debug=True ):
    return _varByTurf( typ='pathExists', component=component, activity=activity, isVersion=False, debug=debug )
