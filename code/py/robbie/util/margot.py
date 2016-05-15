'''
util.margot module
'''

import os
import glob
import shutil
import threading
import cPickle as pickle
import robbie.util.misc as libmisc
#import meadow.lib.calendar as cal
#import meadow.lib.context as libcx
#import meadow.run.util as run_util
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger

_getMargotRootLock = threading.Lock()
def getMargotRoot( create=True):
    with _getMargotRootLock:
        return _getMargotRoot( create=create)

def _getMargotRoot( create=True):
    '''
    provide space for margot data
    '''
    root = twkval.getenv( 'run_margotRoot' ) or os.getenv( 'QUAD_MARGOT_ROOT' )
    try:
        if create and not os.path.exists( root ):
            libmisc.makeMissingDirs( dirName=root )
    except OSError:
        if not os.path.exists( root ):
            logger.error( 'margot: root does not exist, but get OSError')
            raise
    return root

def getSessionSlice( activity, domain=None, session=None, create=True, debug=True ):
    ''' '''
    domain = domain if domain else twkval.getenv('run_domain')
    session = session if session else twkval.getenv('run_session')

    root  = _getSharedRoot( domain=domain, session=session, create=create )
    path = os.path.join( root, '%s.mmap' % activity )
    if debug:
        logger.debug('session_slice: path=%s', path)
    return path

def _getSharedRoot( domain, session, create=True ):
    ''' '''
    varDir = os.path.join( getMargotRoot(), 'shared', domain, session )

    if create:
        libmisc.makeMissingDirs( dirName=varDir )
    return varDir

def _getRoot( compName, debug=False ):
    ''' find margot path '''    
    dn      = getMargotRoot()
    run_tag = str( twkval.getenv( 'run_tag' ) )
    comps   = set( [  'bob', 'run', 'command', 'bloomberg', 'calibs' ] )
    
    if compName in comps:
        path    = os.path.join( dn, compName, run_tag )
    else:
        raise ValueError( 'Unknown compName=%s' % compName )
    
    if debug:
        logger.debug( '_getRoot: compName=%s path=%s' % ( compName, path ) )
    return path

# def listTags( compName, debug=False ):
#     ''' list all tags '''
#     dn = getMargotRoot()
#
#     if compName == 'bob':
#         paths   = glob.glob( os.path.join( dn, compName, '*' ) )
#         tags    = [ os.path.split( path )[-1] for path in paths ]
#
#         if debug:
#             logger.debug( 'margot::listTags dn=%s tags=%s' % ( dn, str( tags ) ) )
#
#         return tags
#
#     raise ValueError( 'Unknown compName=%s' % compName )
#
# def rmCurrTag( debug=True ):
#     ''' remove current tag (tree) '''
#     dn = os.path.join( getMargotRoot(), twkval.getenv( 'run_tag' ) )
#     if debug:
#         logger.debug( 'margot::rmCurrTag dn=%s' % dn )
#
#     if os.path.exists( dn ):
#         shutil.rmtree( dn )
#
# def getRoot( compName, create=True, debug=False ):
#     ''' create directory structure
#         compName = [ bob | cached-calibs ]
#         margot/bob/init
#     '''
#     path    = _getRoot( compName=compName, debug=debug )
#     if create:
#         libmisc.makeMissingDirs( dirName=path )
#
#     return path
#
# def checkRootExists( compName ):
#     ''' check directory structure exists '''
#     return os.path.exists( _getRoot( compName=compName ) )
#
# def getBobJobRoot( bobJobName, create=True ):
#     root = getRoot( compName='bob', sub=bobJobName, create=create )
#     return root
#
# '''
# cached APIs
# '''
#
# def getCacheRoot():
#     ''' get cache root '''
#     dn = getMargotRoot()
#     return dn
#
# def _pathCached( mode, strategyName, calibDate, debug=True ):
#     ''' path to cache '''
#     calibDate   = str( int( calibDate ) )
#     dn          = getCacheRoot( )
#
#     if debug:
#         logger.debug( '_pathCached: %s' % str( ( dn, 'calibs', strategyName, mode, calibDate ) ) )
#
#     return os.path.join( dn, 'calibs', strategyName, mode, calibDate )
#
# def reMapServiceModes( mode ):
#     if mode == 'sim-seed-perse':
#         mode = 'sim-seed'
#     return mode
#
# def findSeedCache(mode, strategyName, calibDate, prevCalibDate, debug = True ):
#     ''' find seeding cache '''
#
#     if mode == 'sim-seed':
#         # sim-seed can be seeded either by the previous day trade-prod, or by sim
#         # check if the previous trade-prod exists
#         sourceMode='trade-prod'
#         dn = _pathCached( mode=sourceMode, strategyName=strategyName, calibDate=prevCalibDate, debug=debug )
#         if os.path.exists( dn ):
#             return sourceMode, dn
#
# #        sourceMode='sim-seed'
# #        dn = _pathCached( mode=sourceMode, strategyName=strategyName, calibDate=prevCalibDate )
# #        if os.path.exists( dn ):
# #            return sourceMode, dn
#
#         sourceMode = 'sim'
#         dn = _pathCached( mode=sourceMode, strategyName=strategyName, calibDate=prevCalibDate, debug=debug  )
#         if os.path.exists( dn ):
#             return sourceMode,  dn
#
#         raise ValueError( 'There is no seeding directory for %s' % str( ( mode, strategyName, calibDate, prevCalibDate ) ) )
#
#     elif mode == 'trade-prod':
#         # check if the current sim-seed exists. trade-prod can be seeded only by sim-seed
#         sourceMode = 'sim-seed'
#         dn = _pathCached( mode=sourceMode, strategyName=strategyName, calibDate=calibDate, debug=debug  )
#         if os.path.exists( dn ):
#             return sourceMode, dn
#
#         raise ValueError( 'There is no seeding directory for %s' % str( ( mode, strategyName, calibDate, prevCalibDate ) ) )
#
#     elif mode == 'sim-prod':
#         # check if the current sim-seed exists. sim-prod can be seeded only by sim-seed
#         sourceMode = 'sim-seed'
#         dn = _pathCached( mode=sourceMode, strategyName=strategyName, calibDate=calibDate, debug=debug  )
#         if os.path.exists( dn ):
#             return sourceMode, dn
#
#         raise ValueError( 'There is no seeding directory for %s' % str( ( mode, strategyName, calibDate, prevCalibDate ) ) )
#
#     raise ValueError( 'There is no seeding directory for %s' % str( ( mode, strategyName, calibDate, prevCalibDate ) ) )
#
# def pathCached( mode, strategyName, calibDate, dataName, createDir=True, debug=True ):
#     ''' path to cache '''
#     dn = _pathCached( mode=mode, strategyName=strategyName, calibDate=calibDate, debug=debug  )
#     exists = True
#     if not os.path.exists( dn ):
#         exists = False
#         if createDir:
#             libmisc.makeMissingDirs( dirName=dn )
#     return exists, dn
#
# def fileNameCached( dirName, dataName ):
#     ''' file name for the dataName '''
#     return os.path.join( dirName, dataName + '.pkl' )
#
# def saveCached( mode, strategyName, calibDate, dataName, dataVals ):
#     ''' save calibs '''
#
#     _exists, dn = pathCached( mode, strategyName, calibDate, dataName, createDir=True )
#
#     fp = fileNameCached( dirName=dn, dataName=dataName )
#
#     if os.path.exists( fp ):
#         logger.debug( 'saveCached: already exists (%s,%s,%s,%s)' % ( mode, strategyName, calibDate, dataName ) )
#     else:
#         logger.debug( 'saveCached: saving (%s,%s,%s,%s)' % ( mode, strategyName, calibDate, dataName ) )
#
#     with open( fp, 'wb' ) as fd:
#         pickle.dump( dataVals, fd, pickle.HIGHEST_PROTOCOL )
#
# def cachedPathsSpecs( mode, strategyName, calibDate, prevCalibDate, dataName, debug=False ):
#     ''' path/spec to cached calibs '''
#
#     paths = []
#
#     calibDate, prevCalibDate = str( int( calibDate ) ), str( int( prevCalibDate ) )
#
#     if mode == 'sim-seed':
#
#         run_execMode = twkval.getenv( 'run_execMode' )
#         if not run_execMode:
#             raise ValueError( 'Undefined run_execMode=%s' % str( run_execMode ) )
#
#         paths.append( fileNameCached(
#             dirName  = _pathCached( mode=run_execMode, strategyName=strategyName, calibDate=prevCalibDate, debug=debug ),
#             dataName = dataName ) )
#
#         paths.append( fileNameCached(
#             dirName  = _pathCached( mode='sim', strategyName=strategyName, calibDate=prevCalibDate, debug=debug ),
#             dataName = dataName ) )
#
#         specs = (
#             ( run_execMode, strategyName, prevCalibDate ) ,
#             ( 'sim', strategyName, prevCalibDate  ),
#         )
#
#     elif mode in ( 'trade-prod', 'sim-prod' ):
#
#         paths.append( fileNameCached(
#             dirName  = _pathCached( mode='sim-seed', strategyName=strategyName, calibDate=calibDate, debug=debug ),
#             dataName = dataName ) )
#
#         specs = ( 'sim-seed', strategyName, calibDate ),
#
#     elif mode == 'sim-prod-cont':
#         # this is a special mode
#         # it is used within sim-prod mode to load data from the previous day's sim-prod
#         # CurrPort and SODPort for today are populated using this mode
#
#         paths.append( fileNameCached(
#             dirName  = _pathCached( mode='sim-prod', strategyName=strategyName, calibDate=prevCalibDate, debug=debug ),
#             dataName = dataName ) )
#
#         specs = ( 'sim-prod', strategyName, calibDate ),
#
#     elif mode == 'sim-seed-perse':
#         # this is a special mode
#         # it is used when we simply need to load data for that 'parent' mode
#
#         paths.append( fileNameCached(
#             dirName  = _pathCached( mode='sim-seed', strategyName=strategyName, calibDate=calibDate, debug=debug ),
#             dataName = dataName ) )
#
#         specs = ( 'sim-seed', strategyName, calibDate ),
#
#     elif mode == 'sim':
#         return (), ()
#
#     else:
#         raise ValueError( 'Wrong mode %s' % mode )
#
#     return paths, specs
#
# def prettyPrint( typ, data ):
#     ''' print prettily '''
#
#     if typ == 'CachePath':
#         dn = getCacheRoot( )
#         if dn in data:
#             return data[ len(dn)+1: ]
#         return data
#     else:
#         raise ValueError( 'Unknown type=%s' % str( typ ) )
#
# def findMostRecent( begDate, strategyName, modes, farInThePast=100, dataName='CachedCalibs' ):
#     found   = dict( ( m,0 ) for m in modes )
#     ccs     = {}
#     counter = 0
#
#     while sum( found.values() ) != len( modes ) and counter < farInThePast:
#         tradeDate       = begDate
#         prevCalibDate   = cal.bizday(dt=tradeDate, specs='-1b')
#
#         for mode in modes:
#             if found[mode]:
#                 continue
#             cc = loadCached( mode=mode, strategyName=strategyName, calibDate=tradeDate, prevCalibDate=prevCalibDate, dataName=dataName, debug=False, throw=False )
#             if cc:
#                 found[ mode ] = 1
#                 ccs[ mode ] = ( begDate, prevCalibDate, cc )
#         begDate = cal.bizday(dt=begDate, specs='-1b' )
#         counter += 1
#
#     return ccs
#
# def loadCached( mode, strategyName, calibDate, prevCalibDate, dataName, debug=False, throw=True ):
#     ''' load cached calibs '''
#     paths, specs = cachedPathsSpecs(
#                         mode           = mode,
#                         strategyName   = strategyName,
#                         calibDate      = calibDate,
#                         prevCalibDate  = prevCalibDate,
#                         dataName       = dataName, debug=debug )
#
#     cachedCalibs    = {}
#     existsCount     = 0
#     for path, spec in zip( paths, specs ):
#         if os.path.exists( path ):
#             existsCount += 1
#
#     if existsCount > 1:
#         msg = 'Two options exist=%s at \n%s' % ( str( specs ), '\n'.join( paths ) )
#         logger.error( msg )
#         if throw:
#             raise ValueError( msg )
#
#     with libcx.Timer('load cache') as timer:
#         for path, spec in zip( paths, specs ):
#             if os.path.exists( path ):
#                 if debug:
#                     logger.debug( 'loadCached: loading %s spec=%s' % ( path, spec ) )
#                 else:
#                     logger.debug( 'loadCached: loading %s spec=%s' % ( prettyPrint( typ='CachePath', data=path ), spec ) )
#                 with open( path, 'rb' ) as fd:
#                     cachedCalibs = pickle.load( fd )
#                     cachedCalibs[ 'OriginSpec' ] = spec
#                 break
#             else:
#                 if debug:
#                     logger.debug( 'loadCached: checking %s' % prettyPrint( typ='CachePath', data=path ) )
#
#     if existsCount > 0:
#         if debug:
#             logger.debug( 'loadCached: pickle.load: %s' % timer.elapsed() )
#
#     mode = reMapServiceModes( mode )
#
#     if not cachedCalibs and mode != 'sim':
#         s = ''
#         for path, spec in zip( paths, specs ):
#                 s += '%s\n' % prettyPrint( typ='CachePath', data=path )
#         msg = '%s cannot find cached calibs. \nLooked in:\n%s' % ( mode, s )
#         logger.error( msg )
#         if throw:
#             raise ValueError( msg )
#         else:
#             return None
#
#     if not cachedCalibs and mode == 'sim':
#         cachedCalibs = {}
#
#     dirName = os.path.join(
#                 _pathCached( mode=mode, strategyName=strategyName, calibDate=calibDate, debug=debug ),
#                 'augment'
#                 )
#
#     specs = ( mode, strategyName, calibDate )
#     cachedCalibs.update( run_util.augmentVars( specs=specs, dirName=dirName ) )
#     return cachedCalibs
#
# def addKey( mode, strategyName, calibDate, key, val, override ):
#     ''' add pickle augment '''
#     dirName = os.path.join(
#                 _pathCached( mode=mode, strategyName=strategyName, calibDate=calibDate ),
#                 'augment'
#                 )
#     libmisc.makeMissingDirs( dirName )
#     path = os.path.join( dirName, '%s.pkl' % key )
#     if not override and os.path.exists( path ):
#         raise ValueError( 'path=%s exists. Can not override.' % path )
#     with open( path, 'wb' ) as fd:
#         pickle.dump(val, fd, pickle.HIGHEST_PROTOCOL )
#     logger.debug( '%s saved to %s' % ( key, prettyPrint( typ='CachePath', data=path ) ) )
#
# def hasKey( mode, strategyName, calibDate, key, debug=False ):
#     ''' check for a pickle augment '''
#
#     mode = reMapServiceModes( mode )
#
#     comDir = os.path.join(
#         _pathCached( mode=mode, strategyName=strategyName, calibDate=calibDate ),
#         'augment'
#         )
#
#     compPath = fileNameCached( dirName=comDir, dataName=key )
#     return os.path.exists( compPath )
#
# # trade ----------------------------
#
# def storeTradeCommand( name, value, override, debug=False ):
#     return storeComponent( compName='command', name=name, value=value, override=override, debug=debug )
#
# def consumeTradeCommand( name, debug=False ):
#     return consumeComponent( compName='command', name=name, debug=debug )
#
# def loadTradeCommand( name, debug=False ):
#     return loadComponent( compName='command', name=name, debug=debug )
#
# def listTradeCommand( debug=False ):
#     return listComponent( compName='command', debug=debug )
#
# # trade ----------------------------
#
# def storeInitialStrategyExposure( fullExp, override, debug=False ):
#     return storeComponent( compName='run', name='istrategyexposure', value=fullExp, override=override, debug=debug )
#
# def loadInitialStrategyExposure( debug=False, throw=True ):
#     return loadComponent( compName='run', name='istrategyexposure', debug=debug, throw=throw )
#
# def storeInitialExposure( fullExp, override, debug=False ):
#     return storeComponent( compName='run', name='iexposure', value=fullExp, override=override, debug=debug )
#
# def loadInitialExposure( debug=False, throw=True ):
#     return loadComponent( compName='run', name='iexposure', debug=debug, throw=throw )
#
# def storeInitialPrice( fullExp, override, debug=False ):
#     return storeComponent( compName='run', name='iprice', value=fullExp, override=override, debug=debug )
#
# def storeInitialMIDS( mids, debug, override ):
#     return storeComponent( compName='run', name='mids', value=mids, override=override, debug=debug )
#
# def loadInitialPrice( debug=False, throw=True ):
#     return loadComponent( compName='run', name='iprice', debug=debug, throw=throw )
#
# def loadInitialMIDs( debug=False, throw=True ):
#     return loadComponent( compName='run', name='mids', debug=debug, throw=throw )
#
# def listComponent( compName, debug=False ):
#     ''' the target and target.ready should exist '''
#     dn      = getRoot( compName=compName, create=True )
#     pattern = os.path.join( dn, '*.ready' )
#     paths   = glob.glob( pattern )
#
#     if debug:
#         logger.debug( 'listComponent dn=%s pattern=%s' % ( dn, str( pattern ) ) )
#         logger.debug( 'listComponent paths=%s' % ( str( paths ) ) )
#
#     targets = []
#     for path in paths:
#         dn0, f  = os.path.split( path )
#         t, _e0  = os.path.splitext( f )
#         t1, _e1 = os.path.splitext( t )
#         tp      = os.path.join( dn0, t )
#         if os.path.exists( tp ):
#             targets.append( t1 )
#
#     if targets or debug:
#         logger.debug( 'listComponent dn=%s ready=%s' % ( dn, str( targets ) ) )
#
#     return targets
#
# def storeComponent( compName, name, value, override, debug=False ):
#     ''' store run component'''
#
#     dn  = getRoot( compName=compName, create=True )
#     path= os.path.join( dn, '%s.pkl' % name )
#
#     if debug:
#         logger.debug( '%s: %s' % ( name, path ) )
#
#     if not override and os.path.exists( path ):
#         raise ValueError( 'path=%s exists. Can not override.' % path )
#
#     with open( path, 'wb' ) as fd:
#         pickle.dump( value, fd, pickle.HIGHEST_PROTOCOL )
#
#     path= os.path.join( dn, '%s.pkl.ready' % name )
#     with open( path, 'wb' ) as fd:
#         fd.write( 'ready' )
#
# def storeNumberedComponent( compName, name, value, debug=False ):
#     ''' store run component'''
#     max_ = 1000
#     dn   = getRoot( compName=compName, create=True )
#     for count in range( max_ ):
#         path= os.path.join( dn, '%s_%d.pkl' % ( name, count ) )
#
#         if os.path.exists( path ):
#             if debug:
#                 logger.debug( 'storeNumberedComponent %s %d: %s' % ( name, count, path ) )
#             break
#
#     if max_ - 1 == count:
#         raise ValueError( 'storeNumberedComponent: Can not allocate a trade file for $s %s' % ( compName, name ) )
#
#     with open( path, 'wb' ) as fd:
#         pickle.dump( value, fd, pickle.HIGHEST_PROTOCOL )
#
#     path= os.path.join( dn, '%s_%d.pkl.ready' % ( name, count ) )
#     with open( path, 'wb' ) as fd:
#         fd.write( 'ready' )
#
# def consumeComponent( compName, name, debug=False ):
#     ''' consume a margot component'''
#
#     dn      = getRoot( compName=compName, create=True )
#     path    = os.path.join( dn, '%s.pkl' % name )
#     used    = os.path.join( dn, '%s.pkl.used' % name )
#
#     if debug:
#         logger.debug( 'consumeComponent: %s: %s' % ( name, path ) )
#
#     if os.path.exists( path ):
#         shutil.move( src=path, dst=used )
#         logger.debug( 'consumeComponent: moved %s %s -> %s' % ( name, path, used ) )
#
# def loadComponent( compName, name, debug=False, throw=True ):
#     ''' load margot component'''
#
#     dn  = getRoot( compName=compName, create=False )
#     path= os.path.join( dn, '%s.pkl' % name )
#
#     if not throw:
#         if not os.path.exists( path ):
#             logger.error( '%s: does not exist %s' % ( name, path ) )
#             return None
#
#     if debug:
#         logger.debug( 'loadComponent: path=%s' % path )
#
#     with open( path ) as fd:
#         return pickle.load( fd )
#
# def loadBloombergEODMark( asType='price_dict', debug=False, throw=True ):
#     ''' load margot bloomberg component'''
#     import meadow.bloomberg.bloombergPrices as bloombergPrices
#     compName    = 'bloomberg'
#     dn          = getRoot( compName=compName, debug=debug, create=False )
#     path        = os.path.join( dn, 'lastPrices.csv' )
#
#     if debug:
#         logger.debug( 'loadBloombergEODMark: path=%s' % ( path ) )
#
#     if not throw:
#         if not os.path.exists( path ):
#             logger.error( 'loadBloombergEODMark: does not exist path=%s' % ( path ) )
#             return None
#
#     if debug:
#         logger.debug( 'loadBloombergEODMark: path=%s' % path )
#
#     with open( path ) as fd:
#         if asType == 'txt':
#             val = fd.read()
#         elif asType == 'price_dict':
#             val = bloombergPrices.loadAs( path, dataType=asType, symbolType='ticker' )
#         else:
#             raise ValueError( 'Unknown asType=%s' % str( asType ) )
#
#     return val
#
# def schedModels( models, debug=False, override=False ):
#     ''' store models for the run '''
#     return storeComponent( compName='run', name='models', value=models, override=override, debug=debug )
#
# def getModels( debug=False, throw=True ):
#     return loadComponent( compName='run', name='models', debug=debug, throw=throw )
#
# def loadVerificationExceptions( debug=False, throw=True ):
#     return loadComponent( compName='run', name='verification_exceptions', debug=debug, throw=throw )
#
# def storeVerificationExceptions( exception, debug=False, override=False ):
#     ''' store models for the run '''
#     return storeComponent( compName='run', name='verification_exceptions', value=exception, override=override, debug=debug )
#
# def getStorageRoot(stratName, name):
#     today = twkval.getenv('run_tag')
#
#     rootDir = getMargotRoot()
#     rootDir = os.path.join(rootDir, 'storage', today, stratName)
#     libmisc.makeMissingDirs( dirName=rootDir )
#     fname = os.path.join(rootDir, name + '.pkl')
#     return fname
#
# def getSharedRoot( domain, instance, create=True ):
#     ''' '''
#     varDir = os.path.join( getMargotRoot(), 'shared', domain, instance )
#
#     if create:
#         libmisc.makeMissingDirs( dirName=varDir )
#     return varDir
#
# def getSharedVar( domain, instance, varName, create=True ):
#     ''' '''
#     varDir  = getSharedRoot( domain=domain, instance=instance, create=create )
#     varPath = os.path.join( varDir, '%s.mmap' % varName )
#     return varPath
#
# def getCachedValue( strategyName, valName, mode=None, calibDate=None ):
#     if not calibDate:
#         calibDate   = cal.today()
#     prevCalibDate   = cal.bizday( calibDate, '-1b' )
#     dataName        = 'CachedCalibs'
#
#     mode = mode if mode else 'sim-prod'
#
#     cachedCalibs    = loadCached(
#                         mode            = mode,
#                         strategyName    = strategyName,
#                         calibDate       = calibDate,
#                         prevCalibDate   = prevCalibDate,
#                         dataName        = dataName,
#                         debug           = True )
#
#     return cachedCalibs[ valName ]
#
# def getCachedValueAsUser( strategyName, turf, valueName, date, asUser ):
#     import meadow.lib.config as libconf
#     date    = date if date else cal.today()
#
#     if twkval.getenv( 'env_userName' ) == asUser:
#         tweaks = {}
#     else:
#         wnDir   = libconf.get( turf=turf, component='bob', sub='margotRoot' )[ asUser ]
#         tweaks  = { 'run_margotRoot': wnDir }
#
#     with twkcx.Tweaks( **tweaks ):
#         return getCachedValue(strategyName = strategyName,
#                                valName = valueName,
#                                calibDate =  date)
#
# def getModelsAsUser( asUser, turf, debug=False, throw=True ):
#     import meadow.lib.config as libconf
#
#     if twkval.getenv( 'env_userName' ) == asUser:
#         tweaks = {}
#     else:
#         wnDir   = libconf.get( turf=turf, component='bob', sub='margotRoot' )[ asUser ]
#         tweaks  = { 'run_margotRoot': wnDir }
#
#     with twkcx.Tweaks( **tweaks ):
#         return getModels( debug = debug, throw = throw )
#
# def getCachedAsUser( strategyName, tradeDate=None, asUser=None, mode=None, debug=True ):
#     import meadow.lib.config as libconf
#     tradeDate   = tradeDate if tradeDate else cal.today()
#     mode        = mode if mode else 'sim-prod'
#     asUser      = asUser if asUser else twkval.getenv( 'env_userName' )
#     turf        = twkval.getenv( 'run_turf' )
#     pCalibDate  = cal.bizday( tradeDate, '-1b' )
#     dataName    = 'CachedCalibs'
#
#     if twkval.getenv( 'env_userName' ) == asUser:
#         tweaks = {}
#     else:
#         wnDir   = libconf.get( turf=turf, component='bob', sub='margotRoot' )[ asUser ]
#         tweaks  = { 'run_margotRoot': wnDir }
#
#     with twkcx.Tweaks( **tweaks ):
#         cachedCalibs    = loadCached(
#                             mode            = mode,
#                             strategyName    = strategyName,
#                             calibDate       = tradeDate,
#                             prevCalibDate   = pCalibDate,
#                             dataName        = dataName,
#                             debug           = debug )
#     return cachedCalibs
