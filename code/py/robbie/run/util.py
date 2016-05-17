import os
import glob
import numpy
import pickle
import pprint
import datetime
import robbie.util.io as io
from   robbie.util.logging import logger
import robbie.util.misc as libmisc

def pair2csv( key, val ):
    if isinstance( val, ( int, float, str, datetime.date, datetime.datetime ) ):
        return '%s\n%s\n' % ( str( key ), str( val ) )
    elif isinstance( val, ( tuple, list, numpy.ndarray ) ):
        return '%s\n%s\n' % ( str( key ), io.arr2csv( val ) )

def dumpTxt( obj, fd ):
    if isinstance( obj, numpy.ndarray ):
        obj = obj.tolist()        
    elif isinstance( obj, ( list, tuple ) ):
        obj = pprint.pformat( obj, depth=100 )        
    fd.write( str( obj ) )

def loadFloatCsv( fd ):
    nums = [float(e) for e in fd.read().split(',') ]
    return nums
    
_dumperConverters = { 
    'pkl'    : ( 'pkl', pickle.dump ),
    'pickle' : ( 'pkl', pickle.dump ),
    'csv'    : ( 'csv', None ),
    'txt'    : ( 'txt', dumpTxt ),
}

_loaderConverters = { 
    'pkl'    : ( 'pkl', pickle.load ),
    'pickle' : ( 'pkl', pickle.load ),
    'csv'    : ( 'csv', loadFloatCsv ),
    'txt'    : ( 'txt', None ),
}

def fileDumperPathGen( dirName, subDir, fileCore, asExt ):
    global _dumperConverters
    if isinstance( asExt, str ):
        asExt = [ asExt ]
        
    for asExt_ in asExt:
        ext, converter = _dumperConverters[ asExt_ ]
        varDir = os.path.join( dirName, subDir )
        yield ( varDir, os.path.join( varDir, '%s.%s' % ( fileCore, ext ) ), converter ) 

def fileLoaderPathGen( dirName, subDir, fileCore, asExt ):
    global _loaderConverters
    if isinstance( asExt, str ):
        asExt = [ asExt ]
        
    for asExt_ in asExt:
        ext, converter = _loaderConverters[ asExt_ ]
        yield ( os.path.join( dirName, subDir, '%s.%s' % ( fileCore, ext ) ), converter ) 

def dumpVars( dirName, fileName, options ):
    with open( os.path.join( dirName, fileName ) ) as fd:
        for key, val in pickle.load( fd ).iteritems():
            for varDir, path, converter in fileDumperPathGen( dirName=dirName, subDir='split', fileCore=key, asExt=( 'txt', 'pkl' ) ):
                libmisc.makeMissingDirs( dirName=varDir )
                logger.debug( 'path=%s convert=%s' % ( key, converter ) )
                if options[ 'ThrowIfOverride' ] and os.path.exists( path ):
                    raise ValueError( 'File already exists path=%s' % path )
                with open( path, 'wb' ) as fdKey:
                    converter( val, fdKey )

def augmentVars( specs, dirName ):
    
    ''' 
        1. load base var (dictionary), and then 
        2. augment some of its keys, if specified
            the typical use is to augment (change) 
            the Portfolio with the EOD-Portfolio for use in the next day 
    '''

    content = {}
    
    for path in glob.glob( os.path.join( dirName, '*.pkl' ) ):
        _dn, fn = os.path.split( path )
        key, _ext = fn.split('.')
        logger.debug( 'pkl augment: %35s %s' % ( io.arr2csv( specs, vs=' ' ), key ) )
        with open( path ) as fdKey:
            val = pickle.load( fdKey )
            content[ key ] = val

    for path in glob.glob( os.path.join( dirName, '*.csv' ) ):
        _dn, fn = os.path.split( path )
        key, _ext = fn.split('.')
        logger.debug( 'csv augment: %s' % key )
        with open( path ) as fdKey:
            val = loadFloatCsv( fdKey )
            content[ key ] = val
        
    return content
    