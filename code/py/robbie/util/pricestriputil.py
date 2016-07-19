import os
import traceback
import subprocess

import numpy

#import util.bbgutil as bbgutil
import robbie.tweak.value as twkval
#import robbie.util.space as libspace
#import robbie.util.config as libconf
from   robbie.util.logging import logger
#import robbie.util.environment as environment

import robbie.turf.util as turfutil
import robbie.tweak.context as twkcx
import robbie.util.symboldb as symboldb
import robbie.echo.pricestrip as pricestrip


'''BID
ASK
LAST_PRICE

IBM US Equity,1
MMM US Equity,2

39491,1

'''

class BBGConfiger( object ):

    def __init__(self, fields, symbols, venues ):
        self._fields    = fields
        self._symbols   = symbols
        self._venues    = venues

    def config(self, stream ):
        for c in self._fields:
            stream.write( c + '\n' )

        stream.write( '\n' )

        for c in self._symbols:
            stream.write( c + '\n' )

        stream.write( '\n' )

        for c in self._venues:
            stream.write( c + '\n' )

        stream.write( '\n' )
        stream.write( '\n' )


bbgFields = (
    'BID',
    'BID_SIZE',
    'BID_UPDATE_STAMP_RT',
    'ASK',
    'ASK_SIZE',
    'ASK_UPDATE_STAMP_RT',
    'EVT_TRADE_PRICE_RT',
    'LAST_PRICE',
    'EVT_TRADE_SIZE_RT',
    'TRADE_UPDATE_STAMP_RT',
)

bbgVenues = ( '39491,1', '39493,2', '39500,3', '14003,4', '14005,5', '14019,6' )

priceArrIx, sizeArrIx   = 0, 1
tradeCntIx, quoteCntIx  = 0, 1

def fakePrices( mode, symbols, marketData ):
    priceArrIx, sizeArrIx   = 0, 1
    
    if mode == 'randint':
        vals = numpy.random.randint( 20, 200, len( symbols ) )
        
        logger.debug( '**fake_bbg! len=%s vals=%s' % ( len(vals), str( vals ) ) )

        trades = numpy.random.randint( 20, 200, len( symbols ) )
        
        marketData[ 'TRADE' ][  priceArrIx ] = trades 
        marketData[ 'TRADE' ][  sizeArrIx  ] = numpy.array( [100] * len( trades ) )
        
        logger.debug( '**fake_bbg! len=%s vals=%s' % ( len(vals), str( vals ) ) )
        
        return vals
    raise ValueError( 'Unknown mode=%s' % mode )

def getMarketDataSlice( marketData, typeName='close', fieldName='price' ):
    ''' converts market data struct in a slice struct'''

    if typeName == 'close':
        typeField = 'TRADE'
    else:
        raise ValueError( 'Unknown typeName=%s' % typeName )

    if fieldName == 'price':
        indexId = priceArrIx
    elif fieldName == 'size':
        indexId = sizeArrIx
    else:
        raise ValueError( 'Unknown typeName=%s' % typeName )
    
    symbols = marketData[ 'MIDS' ]
    
    if twkval.getenv( 'run_fakebbg' ):
        return symbols, fakePrices( mode=twkval.getenv( 'run_fakebbg' ), symbols=symbols, marketData=marketData )        

    vals    = marketData[ typeField ][ indexId ]
    return symbols, vals

def createBBGRun( marketData, flag, streamBlock, debug=False ):

    turf    = twkval.getenv( 'run_turf' )
    env     = libconf.get( turf=turf, component='type' )
    execf   = environment.getApp( env=env, tag='bbg', app='pipe' )

    connect = libconf.getPortHost( turf=turf, component='bbg' )
    appType = libconf.get( turf=turf, component='bbg', sub = 'app_type' )

    domain  = libconf.get( turf=turf, component='marketdata', sub='domain' )
    instance=libconf.get( turf=turf, component='marketdata', sub='instance' )
    rootPath= winston.getSharedRoot( domain=domain, instance=instance, create=True )

    if isinstance( execf, ( list ) ):
        prog    = execf + [ '-h', connect, '-n', appType, '-p', rootPath ]
    else:        
        prog    = [ execf, '-h', connect, '-n', appType, '-p', rootPath ]        
    space   = twkval.getenv( 'bbgp_space' )
    
    def run_():
        mids, msymbs    = libspace.getListedMs( space=space, date=None, alwaysRefresh=True )
        bbgSymbols      = libspace.translateList2Vendor( msymbs, vendor='bbg' )
        eqUsSymbolsIx   = libspace.translateList2Vendor( msymbs, vendor='bbg+full+ix' )

        # need to update
        marketData[ 'MIDS'          ] = mids
        marketData[ 'SPACESYMBOLS'  ] = bbgSymbols
        
        logger.debug('createBBGRun symbols len = %d, %s..%s' % ( len( mids ), str( eqUsSymbolsIx )[:30], str( eqUsSymbolsIx )[-30:] ) )
        logger.debug('createBBGRun prog = %s' % prog )
             
        parser      = bbgutil.BBGOutputLineParser()
        configer    = bbgutil.BBGConfiger( fields=bbgFields, symbols=eqUsSymbolsIx, venues=bbgVenues )
        updater     = bbgutil.BBGUpdater2( cacheData=marketData, header=parser.header( None ), debug=debug )

        ''' start configure and receiver of the bloomberg prices '''
        bbgErrFp    = os.path.join( logger.dirName(), 'bbgerror.txt' )
        with open( bbgErrFp, 'w' ) as fd:
            pipe    = subprocess.Popen( prog, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=fd.fileno() )    

        mktStream   = pipe.stdout
        confStream  = pipe.stdin
        
        pipes = ( confStream, mktStream,  )
        names = ( 'confStream', 'mktStream' )
        
        streamBlock.append( names )
        streamBlock.append( pipes )
        streamBlock.append( pipe )
                        
        logger.debug('createBBGTask config' )
        configer.config( confStream )            
        logger.debug('createBBGTask run %s' % prog )

        parse   = parser.parse
        update  = updater.update
        mkrl    = mktStream.readline
        cont    = flag.cont
        
        while cont:
            _line = mkrl()
            continue

        _terminate( names, pipes, pipe )
                
    return run_

def _terminate( names, pipes, pipe ):
    logger.debug('finishing bbg')
    try:
        pipe.terminate()
    except:
        logger.error( 'got an exception while closing pipe' )
        logger.error(  traceback.format_exc() )
    
    for n,p in zip( names, pipes ):
        try:
            logger.debug( 'closing pipe %s' % n )
            p.close()
        except:
            logger.error( 'got an exception while closing pipe %s' % n )
            logger.error(  traceback.format_exc() )

def createPriceStrip(turf, readOnly):
    # init pricestrip
    priceStripConf    = turfutil.get(turf=turf, component='pricestrip')
    domain  = priceStripConf[ 'domain' ]
    user    = priceStripConf[ 'user'   ]
    tweaks  = {
        'run_domain'    : domain,
        'env_userName'  : user,
    }
    symbols = symboldb.currentSymbols()
    with twkcx.Tweaks( **tweaks ):
        return pricestrip.PriceStrip(readOnly=readOnly, symbols=symbols)
