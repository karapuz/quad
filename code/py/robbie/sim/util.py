import numpy
import datetime
import meadow.lib.misc as libmisc
from   meadow.lib.logging import logger
import meadow.lib.datetime_util as datetime_util

def calibDataSliceMultiBlock( data, params, calibIx, calibWindow, offset, debug = False, onlyDates=False ):
    ret         = {}
    badNames    = ( 'IncludeLast', )
    
    for name in badNames:
        if name in params:
            raise ValueError( 'Should never have %s in a multi-block strategy!' % name )
    
    for blockName, blockVal in data.iteritems():
        blockType = blockName[0]

        if blockType == 'Calib':
            calibBlockName = blockName
            ret[ blockName ] = calibDataSlice( data=blockVal, params=params, calibIx=calibIx, calibWindow=calibWindow, offset=offset )
        else:
            if debug:
                logger.debug( 'slice: skipping %s' % str( blockName ) )

    if onlyDates:
        return ret[ calibBlockName ][ 'dates' ]
    else:        
        return ret
        
def calibDataSlice( data, params, calibIx, calibWindow, offset ):
    ndata   = {}
    slide   = params[ 'Slide' ]
    
    if calibIx < 0:
        raise ValueError( 'CalibIx should be > 0 %s' % calibIx )
    
    for k,m in data.iteritems():
        
        if k in [ 'symbols', 'dataId' ]:
            ndata[ k ] = m
            continue
            
        elif isinstance( m, (int, float, str ) ):
            ndata[ k ] = m
            continue
            
        elif k in [ 'dates' ]:
            if slide:
                ndata[ k ] = m[ calibIx - calibWindow: calibIx+offset ]
            else:
                ndata[ k ] = m[                      : calibIx+offset ]
            continue
        else:
            if slide:
                ndata[ k ] = m[ calibIx - calibWindow : calibIx+offset, : ]
            else:
                ndata[ k ] = m[                       : calibIx+offset, : ]
            continue
            
    return ndata

def tradeDataSlice( data, params, tradeIx ):
    ndata = {}
    for k,m in data.iteritems():
        if k in [ 'symbols', 'dataId' ]:
            ndata[ k ] = m
            continue
            
        elif isinstance( m, (int, float, str ) ):
            ndata[ k ] = m
            continue
        
        elif k in [ 'dates' ]:
            ndata[ k ] = m[ tradeIx ]
            continue
        else:
            ndata[ k ] = m[ tradeIx, : ]
            continue
        
    return ndata


def lastDataSliceMultiBlock( specProcData, tradeDate, debug = False ):
    ret         = {}

    for blockName, blockVal in specProcData.iteritems():
        blockType = blockName[0]

        if blockType in ( 'Update', 'Trade', 'Mrk2Mkt' ):
            dates   = blockVal[ 'dates' ]
            
            if tradeDate not in dates:
                msg = 'no date %s for blockType=%s!' % ( tradeDate, blockType )                
                logger.error( msg )
                raise ValueError( msg )
            
            tradeIx = numpy.where( dates == tradeDate )
            tradeIx = int( tradeIx[0] ) 

            ret[ blockName ] = tradeDataSlice( data=blockVal, params=None, tradeIx=tradeIx )
        else:
            if debug:
                logger.debug( 'last slice: skipping %s for %s' % ( str( blockName ), tradeDate ) )
        
    return ret

def findInitOffset( initialOffset, dates ):
    ''' find offset before! given date '''

    dates   = numpy.array( dates )    
    if isinstance( initialOffset, datetime.date ):
        dtnum   = datetime_util.dt2num( dt=initialOffset, typ='dt' )
    else:
        dtnum   = initialOffset
        
    return int( numpy.searchsorted( dates, [ dtnum ] ) ) - 1

def symbolIndex( baseSymbols, newSymbols ):
    d0 = dict( ( s,i ) for i,s in enumerate( baseSymbols ) )
    cix, lix = zip( * [ (d0[s],i) for i,s in enumerate( newSymbols ) if s in d0 ] )
    return numpy.array( cix ), numpy.array( lix )

def amendCalibWithLatest( schedule, tradeDate, lastSlice, cachedCalib, calibData ):
    ndata   = {}    
    for blocType, blocSpecs, _alais in schedule:

        if blocType != 'Update':
            continue
            
        tradeBlock, calibBlock = blocSpecs
        
        calibKey        = ( 'Calib',  calibBlock )
        lastKey         = ( 'Update', blocSpecs )
        
        calibSymbols    = numpy.array( calibData[ calibKey  ][ 'symbols' ] )
        cachedSymbols   = numpy.array( cachedCalib[ 'symbols' ] )
        lastSymbols     = lastSlice[  lastKey  ][ 'symbols' ]

        cachedSymLen    = len( cachedSymbols )

        chix0, lix0      = symbolIndex( baseSymbols=cachedSymbols, newSymbols=lastSymbols )
        chix1, cix1      = symbolIndex( baseSymbols=cachedSymbols, newSymbols=calibSymbols )
        
        # the Update data now has both the update, and the original data
        ndata[ calibKey ] = calibData[ calibKey ]
        
        ndata[ blocType, blocSpecs ] = {}
        mdata = ndata[ blocType, blocSpecs ]
        for k,m in lastSlice[ lastKey ].iteritems():
            if k == 'symbols':
                mdata[ k ] = cachedSymbols
                continue
            
            elif k ==  'dataId':
                mdata[ k ] = m + list( tradeBlock )
                continue

            elif k ==  'dates':
                mc = calibData[ calibKey ][ k ]
                mdata[ k ] = numpy.append( mc, [ m ] )
                continue
                
            elif isinstance( m, (int, float, str ) ):
                mdata[ k ] = m
                continue

            else:
                mc      = calibData[ calibKey ][ k ]
                
                cached  = numpy.zeros( ( mc.shape[0], cachedSymLen ) )        
                zeros   = numpy.zeros( cachedSymLen )
        
                cached[:, chix1 ] = mc[:, cix1 ]
                zeros [   chix0 ] = m [   lix0 ]
        
                zeros   = numpy.reshape( zeros, ( 1, len( zeros ) ) )
        
                mdata[ k ] = numpy.append( cached, zeros, 0 )
                 
                mdata[ 'UpdateSymbols'] = cachedSymbols

    return ndata


def updatePortfolio( tradedPos, cachedCalib, typ=None ):
    ''' update portfolio '''
    
    portSymbols = cachedCalib[ 'symbols' ]
    if typ == 'CurrPort':
        currPort    = cachedCalib[ 'CurrPort' ]
    elif typ == 'SODPort':
        currPort    = cachedCalib[ 'SODPort' ]
    else :
        raise ValueError( 'Unknown type = %s' % typ )
    shares      = tradedPos[ 'TradeShares'      ]
    symbols     = tradedPos[ 'TradeSymbols'     ]

    d0 = dict( ( n,i ) for ( i,n ) in enumerate( portSymbols) )
    ix = [ d0[n] for n in symbols ]
    
    currPort[ ix ] += shares

def getMarketPrice( symbols, blockVal ):
    blockprice      = blockVal[ 'adjclose'  ]
    blocksymbols    = blockVal[ 'symbols'   ]
    price           = numpy.zeros( len( symbols ) )
     
    d0 = dict( (n,i) for (i,n) in enumerate( blocksymbols ) )
    for i,n in enumerate( symbols ):
        price[i] = blockprice[d0[n]]
    return price
    
def getAvgTradePrice(multiPeriodTrades):
    ''' compute various stats for multi-period trades '''
    totalTransactionCosts, totalshiftedAccCosts, totalDol, totalShares = 0, 0, 0, 0
    
    for trades in multiPeriodTrades:
        totalTransactionCosts += trades['TransactionCosts']
        totalshiftedAccCosts  += trades['shiftedAccCosts']
        
        totalDol    += trades['TradeShares'] * trades['TradePrices']
        totalShares += trades['TradeShares']
    
    firstTrades         = multiPeriodTrades[0]
    
    shareix             = (totalShares!=0)
    avgPrice            = numpy.zeros( len(totalShares) )  
    avgPrice[shareix]   = totalDol[ shareix ] / totalShares[ shareix ]
    avgShiftedCosts     = ( avgPrice - firstTrades[ 'LastPrices' ] ) * totalShares
    symbols             = firstTrades[ 'TradeSymbols' ]
    preprice            = firstTrades['LastPrices']
    totalShareInfo= { 
     'TradeShares' : totalShares,
     'TradeSymbols': symbols,
     }
    return symbols, totalShares, avgPrice, preprice, totalTransactionCosts, avgShiftedCosts, totalShareInfo

def delColDictMat( rets, masks, allNameTypes=None, debug=False, handleUnknown=False ):
    nret = {}
    
    def validateShape( name, mat=None, m=None, n=None ):
        if m:
            if mat.shape[0] != m:
                raise ValueError( 'Bad shape for name=%s shape=%s' % ( name, str( mat.shape ) ) )
        if n:
            if mat.shape[1] != n:
                raise ValueError( 'Bad shape for name=%s shape=%s' % ( name, str( mat.shape ) ) )
    
    for maskName in sorted( masks ):
        
        mask        = masks[ maskName ] 
        nameTypes   = allNameTypes[ maskName ]
        nochange    = nameTypes.get(  'nochange', set() )

        mask = numpy.array( mask ) == 1
        
        for name, val in rets.iteritems():
            # we do not process ints and strs
            if isinstance( val, ( float, int, str ) ) or name in nochange:
                nret[ name ] = val
    
            elif 'colMat' in nameTypes and name in nameTypes[ 'colMat' ]:
                val_ = numpy.array( val )
                if debug:
                    logger.debug( 'colMat before name=%s type=%s shape=%s' % ( name, type(val), val_.shape ))
                validateShape( name, mat=val, m=None, n=len(mask) )
                nret[ name ] = val[ :, mask ]
                if debug:
                    logger.debug( 'colMat after  name=%s shape=%s' % ( name, nret[ name ].shape ))
                
            elif 'rowMat' in nameTypes and name in nameTypes[ 'rowMat' ]:
                # logger.debug( 'before name=%s type=%s shape=%s' % ( name, type(val), val.shape ))
                validateShape( name, mat=val, m=len(mask), n=None )
                nret[ name ] = val[ mask : ]
                if debug:
                    logger.debug( 'rowMat after  name=%s shape=%s' % ( name, nret[ name ].shape ))
    
            elif 'simpleList' in nameTypes and name in nameTypes[ 'simpleList' ]:
                val_ = numpy.array( val )
                if debug:
                    logger.debug( 'simpleList before name=%s type=%s shape=%s' % ( name, type(val), val_.shape ))
                nret[ name ] = ( val_[ mask ] ).tolist()
                if debug:
                    logger.debug( 'simpleList after  name=%s shape=%s' % ( name, nret[ name ].shape ))
    
            elif 'simpleVec' in nameTypes and name in nameTypes[ 'simpleVec' ]:
                val_ = numpy.array( val )

                if debug:
                    logger.debug( 'simpleVec before name=%s type=%s shape=%s' % ( name, type(val), val_.shape ))
                
                nret[ name ] = val_[ mask ]
                    
                if debug:
                    logger.debug( 'simpleVec after  name=%s shape=%s' % ( name, nret[ name ].shape ))
            elif 'tradeIx' in nameTypes and name in nameTypes[ 'tradeIx' ]:
                val_ = numpy.array( val )
                if debug:
                    logger.debug( 'tradaIx before name=%s type=%s shape=%s vals=%s' % ( name, type(val), val_.shape, str( val_[-2:] ) ) )
                
                z               = numpy.zeros(mask.shape, int)
                z[mask==False]  = 1
                z[val_]         = 0
                csz             = numpy.cumsum(z)
                nret[ name ]    = val_-csz[val_]
                val_            = nret[ name ]
                if debug:
                    logger.debug( 'tradaIx after name=%s type=%s shape=%s vals=%s' % ( name, type(val_), val_.shape, str(val_[-2:] ) ) )
                
                
            elif 'vecCompress' in nameTypes and name in nameTypes[ 'vecCompress' ]:
                val_ = numpy.array( nret[ name ] )
                if debug:
                    logger.debug( 'vecCompress before name=%s type=%s shape=%s vals=%s' % ( name, type(val), val_.shape, str( val_[-2:] ) ) )
                
                cix             = numpy.cumsum( mask==False )                 
                nret[ name ]    = ( val_ - cix )[ mask ]
                val_            = nret[ name ]
                if debug:
                    logger.debug( 'vecCompress after name=%s type=%s shape=%s vals=%s' % ( name, type(val_), val_.shape, str(val_[-2:] ) ) )

            elif '2DCompress' in nameTypes and name in nameTypes[ '2DCompress' ]:
                val_ = numpy.array( nret[ name ] )
                if debug:
                    logger.debug( '2DCompress before name=%s type=%s shape=%s vals=%s' % ( name, type(val), val_.shape, str( val_[-2:] ) ) )
                            
                nret[ name ]    = val_[ mask ]
                val_            = nret[ name ]
                if debug:
                    logger.debug( '2DCompress after name=%s type=%s shape=%s vals=%s' % ( name, type(val_), val_.shape, str(val_[-2:] ) ) )

            
            elif 'dict' in nameTypes and name in nameTypes[ 'dict' ]:
                masks_          = { maskName: mask }
                allNameTypes_   = { maskName: nameTypes }
                if debug:
                    logger.debug( 'dict enter name=%s' % ( name ))
                                
                nret[ name ]    = delColDictMat( rets=val, masks=masks_, allNameTypes=allNameTypes_, debug=debug, handleUnknown=handleUnknown )
                
            elif 'tuple' in nameTypes and name in nameTypes[ 'tuple' ]:
    #            nret[ name ][0] = val[0][ mask, : ]    
    #            nret[ name ][1] = val[1][ mask ]    
    #            nret[ name ][2] = val[2][ mask, :, :]
                if name == 'TibRls': 
                    nret[ name ] = ( val[0][ mask, : ], val[1][ mask ], val[2][ mask, :, :], val[3], val[4], val[5])
                elif name == 'TibRlsLead' :
                    nret[ name ] = ( val[0][ mask, : ], val[1][ mask, : ], val[2][ mask ], val[3][ mask, :, :], val[4], val[5], val[6] )
                else:
                    raise ValueError( 'Unknown name=%s' % name )
            
            elif 'empty' in nameTypes and name in nameTypes[ 'empty' ]:
                nret[ name ] = []

            else:
                if handleUnknown:
                    if name not in nret:
                        msg = 'delColDictMat: Unknown name=%s' % name
                        nret[ name ] = val
                    else:
                        msg = 'delColDictMat: Already handled name=%s' % name
                    if debug:
                        logger.debug( msg )
                else:
                    raise ValueError( msg )
    
    return nret

def reusePrevDayData( opMode, strategyName, cachedCalib, tradeDate, calibDate ):
    '''
    this is a helper function - sim-prod for today will re-use exposure from sim-prod of yesterday
    '''
    import meadow.lib.winston as winston
    if opMode=='sim-prod':
        
        pCachedCalib = winston.loadCached(
            mode          = 'sim-prod-cont', 
            strategyName  = strategyName, 
            calibDate     = tradeDate, 
            prevCalibDate = calibDate,
            dataName      = 'CachedCalibs',
            throw         = False, )

        if not pCachedCalib:
            pCachedCalib = winston.loadCached(
                mode          = 'sim-prod', 
                strategyName  = strategyName, 
                calibDate     = tradeDate, 
                prevCalibDate = calibDate,
                dataName      = 'CachedCalibs',
                throw         = True, )
        
        for key in ( 'CurrPort', 'SODPort' ):
            if not winston.hasKey( mode=opMode, strategyName=strategyName, calibDate=tradeDate, key=key, debug=True ):
                val = pCachedCalib[ key ]
                winston.addKey( mode=opMode, strategyName=strategyName, calibDate=tradeDate, key=key, val=val, override=False )
            else:
                logger.debug( 'reusePrevDayData: key=%s for %s exists' % ( key, tradeDate ) )
    else:
        raise ValueError( 'Unknown mode=%s' % str( opMode ) )    

def setLoggerUnderWinston( appName, now ):
    import meadow.tweak.context as twkcx
    import meadow.lib.logging as logging
    
    dn = currentDir( appName=appName, now=now )
    
    with twkcx.Tweaks( env_loggerDir=dn ):
        logging.toFile( app=appName, mode='px' )

_currentDirPath = False
def currentDir( appName, now, debug = False ):
    ''' create default directory '''
    global _currentDirPath
    if _currentDirPath: 
        return _currentDirPath

    import os
    import meadow.lib.winston as winston
    
    for ix in xrange( 1000 ):
        parts = ( 'simulator', ) + appName + ( str( now ), str( ix ) )
        _currentDirPath  = os.path.join( winston.getWinstonRoot(), *parts )
        if not os.path.exists( _currentDirPath ):
            break
        
    libmisc.makeMissingDirs( dirName=_currentDirPath )
    logger.debug( 'directing log to dn=%s' % _currentDirPath )
    return _currentDirPath

def listSimProdInternal( name, section, stratName ):
    import os
    import meadow.lib.winston as winston
    import meadow.tweak.value as twkval
    import meadow.lib.io as io
    import meadow.argus.util as argusutil
    tradeDate   = str( twkval.getenv( 'run_tradeDate' ) )
    mode        = 'sim-prod'    
    rootDir = os.path.join( winston.getWinstonRoot(), 'simulator', stratName, mode, tradeDate )
    dirName, _, _ = io.findLastLeafDir( rootDir, trial=None, debug=True )
    return dirName, argusutil.indexInternal( dirName=dirName, stratName=stratName, section=section, name=name )

def listArgusInternal( name, section, stratName ):
    import os
    import meadow.lib.winston as winston
    import meadow.tweak.value as twkval
    import meadow.lib.io as io
    import meadow.argus.util as argusutil
    tradeDate   = str( twkval.getenv( 'run_tradeDate' ) )        
    rootDir = os.path.join( winston.getWinstonRoot(), 'argus', tradeDate )
    dirName, _, _ = io.findLastLeafDir( rootDir, trial=None, debug=True )
    return dirName, argusutil.indexInternal( dirName=dirName, stratName=stratName, section=section, name=name )

def loadLastInternalLog( rootDir, name, section, stratName ):
    '''
    name='shares_info', section='execution', stratName='EQ_US_CSH' 
    '''
    import meadow.lib.io as io
    import meadow.argus.util as argusutil
    
    # rootDir = '/home/ipresman/projects/winston/simulator/EQ_US_CSH/sim-prod/20130327'
    
    dirName, _, _ = io.findLastLeafDir( rootDir, trial=None, debug=True )
    return argusutil.loadInternal( dirName, stratName, section, name, selectFunc=max )

