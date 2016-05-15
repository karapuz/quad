import os
import glob
import numpy
import threading
import functools

import cPickle as pickle

import meadow.lib.config as libconf
import meadow.tweak.value as twkval
import meadow.tweak.context as twkcx
import meadow.lib.winston as winston
import meadow.lib.logging as logging
import meadow.argus.taskenv as taskenv
import meadow.lib.mmap_array as mmap_array
import meadow.lib.misc as libmisc

import meadow.lib.space as libspace
import meadow.lib.datetime_util as dut 
from   meadow.lib.logging import logger
import meadow.lib.journalling as journalling

class Flag( object ):
    def __init__(self, cont ):
        self.cont = cont

class Request( object ):
    start       = 'START'
    cancel      = 'CANCEL'
    status      = 'STATUS'
    clear       = 'CLEARSTATUS'
    mng         = 'MNG'
    
    splitSymbol = ':'
    specsSplitSymbol = ','
        
    @staticmethod
    def pack( typ, specs ):
        return pickle.dumps( ( typ, specs ) )

    @staticmethod
    def unpack( s ):
        return pickle.loads( s )

def createReq( typ, what, when, how ):
    return Request.pack(  typ,  ( what, when, how ) )

class Status( object ):
    dead    = 'dead'
    alive   = 'alive'
    none    = 'none'

def stateEvolution( stateBefore, stateNow ):
    return '%s->%s' % ( stateBefore, stateNow )

def scheduledTaskName( taskTypeName, taskSchedule ):
    return 'Task=%s@%s' % ( taskTypeName, taskSchedule )

_storeValPrefix = 0
def storeRetVals( logger, taskName, txt ):
    ''' store return vals '''
    global _storeValPrefix
    dn = logger.dirName()
    with open( os.path.join( dn, '%d_%s' % ( _storeValPrefix, taskName ) + '.txt'), 'w' ) as fd:
        fd.write( txt )
    _storeValPrefix += 1

def newTimedThreadedTask( dt, funcName, taskObj, logger ):
    '''
    at time (dt) on every bizday, the system will invoke taskObj.funcName( dt, logger )
    '''
    d = dut.toTimeSec( dt ) - dut.timeNow()
    if d >= 1:
        t = threading.Timer( d, functools.partial( getattr( taskObj, funcName ), dt, logger ) )
        t.start()
        return t, d
    return None, None

def newDateTimedThreadedFuncTask( dt, func, logger ):
    '''
    at time (dt) on every bizday, the system will invoke func( dt, logger )
    '''
    d = dut.toTimeSec( dt, asTime=False ) - dut.timeNow( asTime=False )
    if d >= 1:
        t = threading.Timer( d, functools.partial( func, dt, logger ) )
        t.start()
        return t, d
    return None, None

def formStatus( env, specs, taskData ):    
    if isinstance( specs, ( list, tuple ) ):
        what = specs[0]
    else:
        return 'Wrong type for specs=%s' % str( specs )
    
    if what == 'status':
        return Request.pack( 'status', str( taskData[ 'status' ] ) )
    else:
        return 'Wrong specs=%s' % str( specs )

def contain( p, t ):
    return ( p in t ), t

def notContain( p, t ):
    return ( p not in t) , t

def resetLogger():
    dn = currentDir()
    appName = taskenv.getObj('env', 'application' )
    
    with twkcx.Tweaks( env_loggerDir=dn ):
        logging.toFile( app=appName, mode='px', asMultiThread=True, deamon=True )
    return True, ''

_argusDir = False
def currentDir( debug = False ):
    ''' create default directory '''
    global _argusDir
    if _argusDir: return _argusDir
    
    now = twkval.getenv( 'today' )
    appName = taskenv.getObj('env', 'application' )
    
    for ix in xrange( 1000 ):
        _argusDir  = os.path.join( winston.getWinstonRoot(), appName, str( now ), str( ix ) )
        if not os.path.exists( _argusDir ):
            break
        
    debug = debug or twkval.getenv( 'argus_debug' )
    libmisc.makeMissingDirs( dirName=_argusDir )
    logger.debug( 'directing log to dn=%s' % _argusDir )
    return _argusDir

def startBbg( server ):
    env         = twkval.getenv( 'run_env' )
    # schedule    = 'allDay'
    schedule    = 'startNowAllDay'
    specs       = ( 'bbg', schedule, '' )
    logger.debug( 'starting %s' % str( specs ) )
    
    server.startTask( env, taskType='bbg', schedName=schedule )
    return True, ''

def startJrnl( server ):
    jrnlRoot = journalling.getJournalRoot()
    twkval.setval( 'jrnl_root', jrnlRoot )
    
    # specs   = ( 'journal', 'allMinutes', '' )
    
    schedule    = 'startNowAllDay'
    env         = twkval.getenv( 'run_env' )
    specs       = ( 'journal', schedule, '' )
    
    logger.debug( 'starting %s' % str( specs ) )    
    server.startTask( env, taskType='journal', schedName=schedule )
    
    return True, ''

def resetServerTimers( server ):
    env     = twkval.getenv( 'run_env' )
    server.clearStatus( env  )
    return True, ''

def resetServer( server ):
    resetLogger()
    resetServerTimers( server )
        
    components  = twkval.getenv( 'exec_components' )
    
    if 'bbg' in components:
        startBbg( server )
        
    if 'jrnl' in components:
        startJrnl( server )

    if 'strat' in components:
        import meadow.argus.strattask as strattask
        logger.debug( 'exec mode' )
        strattask.startStrat( server )
        
    return True, ''

def loadExposure( fp ):
    ''' load an exposure file '''
    ret = []
    with open( fp ) as fd:
        txt = fd.read()
        rows = txt.split('\n')
        for r in rows:
            if r:
                sym, amount = r.split(',')
                ret.append( ( sym, int( amount ) ) )
    return ret

def loadTrade( fp ):
    try:
        return _loadTrade( fp )
    except:
        import traceback
        logger.error( 'loadTrade: %s' % str( fp ) )
        logger.error( traceback.format_exc() )
        
    return []
        
def _loadTrade( fp ):
    ''' load a trade file '''
    ret = []
    with open( fp ) as fd:
        txt = fd.read()
        rows = txt.split('\n')
        for r in rows:
            logger.debug( 'loading r=%s' % str( r ) )
            if not r:
                continue
            
            if r[0] == '#':
                logger.debug( 'comment %s' % str( r ) )
                continue
            
            parts   = r.split(',')
            typ     = parts[0]
            
            if typ == 'M':
                typ, sym, secType, execVenue, qty = r.split(',')                
                line = ( typ, sym, secType, execVenue, int( qty ) )
                
            elif typ == 'L':
                typ, sym, secType, execVenue, qty, price = r.split(',')
                line = ( typ, sym, secType, execVenue, int( qty ), float( price ) )
                
            elif typ in (  'TWAP', 'TWLR_TWAP' ):
                typ, sym, amount, targetTime, targetStep = r.split(',')
                line = ( typ, sym, int( amount ), float( targetTime ) , float( targetStep ) )
                
            else:
                raise ValueError( 'Unknown type %s' % str( typ ) )
            ret.append( line )
    return ret

def getClientRoot( create=True ):
    
    dn  = winston.getWinstonRoot()
    now = str( twkval.getenv( 'today' ) )
    path= os.path.join( dn, 'client', now )
    
    if create:
        libmisc.makeMissingDirs( dirName=path )
    return path 

def getClientFile( fn, ext = '.exp' ):
    dn      = getClientRoot()
    exists  = True
    
    if ext not in fn:
        fn = fn + ext

    fp = os.path.join( dn, fn )
    if os.path.exists( fp ):
        return exists, dn, fn, fp

    return False, dn, fn, fp

_storeInternalIndex = {}
_storeInternalIndex_lock = threading.Lock()

def storeInternal( stratName, section, name, val ):
    ''' store return vals '''
    
    global _storeInternalIndex

    key = ( stratName, section, name )
    with _storeInternalIndex_lock:    
        if key not in _storeInternalIndex:
            _storeInternalIndex[ key ] = 0    
        ix = _storeInternalIndex[ key ]
        _storeInternalIndex[ key ] += 1
    
    dn  = os.path.join( logger.dirName(), stratName, section )
    
    libmisc.makeMissingDirs( dirName=dn )
        
    path = os.path.join( dn, '%s.%d.pkl' % ( name, ix  ) )
    
    if os.path.exists( path ):
        logger.error( 'storeInternal: overriding!!! stratName=%s section=%s name=%s  path=%s' % ( 
                        stratName, section, name, path ) 
        )
    else:
        logger.debug( 'storeInternal: stratName=%s section=%s name=%s path=%s' % ( stratName, section, name, path ))
        
    with open( path, 'wb' ) as fd:
        pickle.dump( val, fd, pickle.HIGHEST_PROTOCOL )

def indexInternal( dirName, stratName, section, name ):
    ''' store return vals '''

    ixs = []
    dn  = os.path.join( dirName, stratName, section )
    if not os.path.exists( dn ):
        return ixs

    pattern = os.path.join( dn, '%s.*.pkl' % ( name ) )
    for path in glob.glob( pattern ):        
        _dirName, fileName = os.path.split( path )
        _core, ix, _ext = fileName.split( '.' )
        ixs.append( int( ix ) )
        
    return ixs

def number_0( x ):
    return 0

def number_1( x ):
    return 1

def number_2( x ):
    return 2

def number_3( x ):
    return 3

def leafPath( dirName, stratName, section, name, ix ):
    return os.path.join( dirName, stratName, section, '%s.%d.pkl' % ( name , ix  ) )

def loadInternal( dirName, stratName, section, name, selectFunc=max ):
    ''' store return vals '''

    ixs     = indexInternal( dirName=dirName, stratName=stratName, section=section, name=name )
    if not ixs:
        raise ValueError( 'Nothing in dirName=%s any stratName=%s section=%s name=%s' % ( 
                    dirName, stratName, section, name ) )
    
    # path = os.path.join( dirName, stratName, section, '%s.%d.pkl' % ( name , selectFunc( ixs ) ) )
    ix = selectFunc( ixs )
    path = leafPath( dirName=dirName, stratName=stratName, section=section, name=name, ix=ix )
    
    if not os.path.exists( path ):
        logger.error( 'storeInternal: can not load!!! stratName=%s section=%s name=%s  path=%s' % ( stratName, section, name, path ))
        return
        
    logger.debug( 'loadInternal: stratName=%s section=%s name=%s  path=%s' % ( stratName, section, name, path ))
    
    with open( path, 'rb' ) as fd:
        return pickle.load( fd )

def newMarketData( readOnly=False, create=True ):
    ''' create new market data object '''
    
    cacheData   = {}
    
    maxSymbols  = libspace.MAX_SYMBOLS
    mdSharing   = twkval.getenv( 'run_mrktDtSharing' )
    turf        = twkval.getenv( 'run_turf' )
    tradeDate   = twkval.getenv( 'run_tradeDate' )
    
    domain      = libconf.get( turf=turf, component='marketdata', sub='domain' )
    tweaks      = {}

    if libconf.exists( turf=turf, component='marketdata', sub='owner' ):
        owner   = libconf.get( turf=turf, component='marketdata', sub='owner' )
        wnDir   = libconf.get( turf=turf, component='bob', sub='winstonRoot' )[ owner ]
        tweaks[ 'run_winstonRoot'] = wnDir
    
    instanceName=libconf.get( turf=turf, component='marketdata', sub='instance' )
    shape       = ( maxSymbols, ) 
    logger.debug( 'newMarketData tweaks = %s' % str( tweaks ) )
    
    with twkcx.Tweaks( **tweaks ):
        varPath = winston.getSharedRoot( domain=domain, instance=instanceName, create=True )

        if readOnly:
            mmapFunc    = mmap_array.newRead
            mmapVersion = mmap_array.getVersion( domain=domain, instance=instanceName, varName=mmap_array.BbgVersion, create=True  )
        else:
            mmapFunc    = mmap_array.new
            mmapVersion = mmap_array.incrVersion( domain=domain, instance=instanceName, varName=mmap_array.BbgVersion )
        
        logger.debug( 'newMarketData mmapVersion=%d readOnly=%s varPath=%s' % ( mmapVersion, readOnly, varPath ) )
        
        for key in ( 'TRADE', 'ASK', 'BID', 'SYMBOL', 'CUM_TRADE', 'TRADE_QUOTE_COUNT', 'LAST_EVENT_TIME' ):
            if key not in cacheData:
                if mdSharing == 'memory':
                    cacheData[ key ] = [ 
                            numpy.empty( maxSymbols ), 
                            numpy.empty( maxSymbols ), 
                            numpy.empty( maxSymbols ), 
                    ]
                elif mdSharing == 'mmap':
                    logger.debug('newMarketData sharing key=%-20s readOnly=%s create=%s' % ( key, readOnly, create ) )
                    cacheData[ key ] = [ 
                        mmapFunc(  domain=domain, instance=instanceName, varName='%s-0' % key, shape=shape ),
                        mmapFunc(  domain=domain, instance=instanceName, varName='%s-1' % key, shape=shape ),
                        mmapFunc(  domain=domain, instance=instanceName, varName='%s-2' % key, shape=shape ),
                    ]
                else:
                    raise ValueError( 'Unknown market sharing regime=%s' % mdSharing )
    
                if create:
                    cacheData[ key ][0][:] = cacheData[ key ][0] * 0 
                    cacheData[ key ][1][:] = cacheData[ key ][1] * 0 
    
        if mdSharing == 'memory':
            cacheData[ 'MIDS' ] = numpy.zeros( maxSymbols )
        elif mdSharing == 'mmap':
            cacheData[ 'MIDS'   ] =  mmapFunc(  domain=domain, instance=instanceName, varName='MIDS', dtype='int', shape=shape )
        else:
            raise ValueError( 'Unknown market sharing regime=%s' % mdSharing )

    if create:
        space   = twkval.getenv( 'bbgp_space' )
        mids, msymbs= libspace.getListedMs( space=space, date=None, alwaysRefresh=True )
        cacheData[ 'MIDS' ][ : ] = numpy.zeros( shape )
        cacheData[ 'MIDS' ][ : len(mids) ] = numpy.array( mids )
    else:
        from meadow.lib.symbChangeDB import symbDB
        mids    = cacheData[ 'MIDS' ]
        msymbs  = [ symbDB.MID2symb( MID=mid, date=tradeDate ) for mid in mids if mid ]
        
    bbgSymbols  = libspace.translateList2Vendor( msymbs, vendor='bbg' )
    cacheData[ 'SPACESYMBOLS'  ] =  bbgSymbols

    for key in ( 'TRADE', 'ASK', 'BID', 'SYMBOL', 'CUM_TRADE', 'TRADE_QUOTE_COUNT' ):
        for vix, val in enumerate( cacheData[ key ] ):
            logger.debug( 'key=%20s vix=%s len=%s' % ( key, vix, len( val ) ) )
    logger.debug( 'shape=%s' % str( shape ) )
    
    return cacheData

def reportMarketDataShape( title, askPriceSize, bidPriceSize ):
    logger.debug( 
        '%s ask %s,%s bid %s,%s' % ( 
                title, 
                len( askPriceSize[0] ), len( askPriceSize[1] ), 
                len( bidPriceSize[0] ), len( bidPriceSize[1] ),  
        ) 
    )
