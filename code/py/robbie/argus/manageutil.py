'''
'''

import os
import numpy
import shutil
import meadow.lib.misc as libmisc
import meadow.lib.calendar as cal
import meadow.tweak.value as twkval
import meadow.lib.winston as winston
import meadow.tweak.context as twkcx
import meadow.allocation.util as alut
from   meadow.lib.logging import logger
import meadow.lib.positionmngmnt as posmng
import meadow.thirdparty.tradar.util as trul

def prettyPrintChecks( allChecks ):
    ''' pretty print all checks '''
    logger.debug( '----------------------------------------------------' )
    for key,val in allChecks.iteritems():
        if isinstance( val, dict ):
            nval = {}
            for k0, val0 in val.iteritems():
                if isinstance( val0, ( set, tuple, list, dict, numpy.ndarray ) ):
                    nval[ k0 ] = 'len=%d' % len( val0 )
                else:
                    nval[ k0 ] = str( val0 )
        else:
            nval = val
            
        s = str( nval )
        logger.debug( '%-20s : %-s' % ( key, s ) )

def checkReadyWithTweaks( tweaks ):
    with twkcx.Tweaks( **tweaks ):
        return _checkReady()
    
def _checkReady():
    allChecks   = {}
    stratNames  = winston.getModels( debug=True, throw=False )
    
    allChecks[ 'sched-model'] = stratNames
    if stratNames == None:
        return allChecks

    # endDate     = twkval.getenv( 'run_tag' )
    tradeDate   = twkval.getenv( 'run_tradeDate' )
    pCalibDate  = cal.bizday(tradeDate, '-1b')
    
    tradarType  = 'tradar-eod'
    allChecks[ 'sim-seed'           ] = {}

    augKeys = ( 
        'CurrPort', 
        'SODPort',
        'restricted-notrade' )
            
    for augKey in augKeys: 
        allChecks[ augKey   ] = {}

    allChecks[ tradarType   ] = trul.initialPos_pathExists( typ='tradar-eod', debug=True )
    
    for stratName in stratNames:
        mode = 'trade-prod'
        cc = winston.loadCached( 
                mode=mode, 
                strategyName=stratName, 
                calibDate=tradeDate, 
                prevCalibDate=pCalibDate, 
                dataName='CachedCalibs', 
                debug=False, throw=False )
        allChecks[ 'sim-seed'][ stratName ] = ( cc != None )
        
        for augKey in augKeys: 
            hasKey = winston.hasKey( mode, strategyName=stratName, calibDate=tradeDate, key=augKey, debug=False )
            if hasKey:
                allChecks[ augKey ][ stratName ] = cc[ augKey ]
            else:
                allChecks[ augKey ][ stratName ] = False

    iExp = winston.loadInitialExposure( throw=False )
    allChecks[ 'init-exp'] = iExp != None
    return allChecks

def sodTradarWithTweaks( override, tweaks, debug ):
    ''' '''
    
    tradarType  = 'tradar-eod'
    
    with twkcx.Tweaks( **tweaks ):        
        _sodPrepareFile( override=override, debug=debug, tradarType=tradarType )        
        return _sodTradar( override=override, debug=debug )

def _sodPrepareFile( tradarType='tradar-eod', override=False, debug=True ):
    ''' '''
    
    winstonDir, winstonPath = trul.initialPos_path( tradarType )
    
    if not os.path.exists( winstonPath ):
        libmisc.makeMissingDirs( dirName=winstonDir )        
        logger.debug('_sodPrepareFile: missing %s' % winstonPath )
        tradarPath = trul.globalPath( function='Outbound', runTag=None )
        logger.debug( '_sodPrepareFile: getting %s from %s' % ( tradarType,  tradarPath ) )
        shutil.copyfile(src=tradarPath, dst=winstonPath)
    else:
        logger.debug('_sodPrepareFile: exists %s' % winstonPath )

def _sodTradar( override, debug, tradarType='tradar-eod' ):
    
    tradeDate   = twkval.getenv( 'run_tradeDate', throwIfNone=True )
    pCalibDate  = cal.bizday(tradeDate, '-1b')
    strats      = winston.getModels( debug=True )
    
    iExp, iPrice, mid2symbol, _blncSheet = trul.initialPos_parse( tradarType )

#    posMids = mid2symbol.keys()
#    _mids, shareRatio, priceRatio = posmng.eod2sod( posMids, len( posMids ) * [1.], len( posMids ) * [1.], tradeDate )
#    mid2priceRatio  = dict( ( mid, r ) for ( mid, r ) in zip( posMids, priceRatio ) )      
#    nPrice  = dict( ( mid, iPrice[ mid ] * mid2priceRatio[ mid ] ) for mid in posMids if mid in iPrice )

    nPrice = {}
    for stratName in strats:
        stratAlias = alut.stratAlias( stratName )
        
        logger.debug( '_sodTradar: stratName=%s stratAlias=%s' % ( stratName, stratAlias ) )
        
        mode    = 'trade-prod'
        calibs  = winston.loadCached( 
                    mode            = mode,
                    strategyName    = stratName, 
                    calibDate       = tradeDate, 
                    prevCalibDate   = pCalibDate, 
                    dataName        = 'CachedCalibs', debug=False, throw=True )
        
        mids    = calibs[ 'symbols' ]

        _mids, shareRatio, priceRatio = posmng.eod2sod( mids, len( mids ) * [1.], len( mids ) * [1.], tradeDate )
        mid2priceRatio  = dict( ( mid, r ) for ( mid, r ) in zip( mids, priceRatio ) )      
        nPrice.update( dict( ( mid, iPrice[ mid ] * mid2priceRatio[ mid ] ) for mid in mids if mid in iPrice ) )
        
        mid2pos = dict( ( mid, ix ) for ( ix, mid ) in enumerate( mids ) )
        currPort= numpy.zeros( mids.shape )
                
        if stratAlias in iExp:        
            for ( _secType, mid, qty ) in iExp[ stratAlias ]:
                if mid not in mid2pos:
                    msg = 'Tradar position is not legit mid=%s symbol=%s qty=%s' % ( mid, mid2symbol[ mid ], qty )
                    logger.error( msg )
                    continue
                currPort[ mid2pos[ mid ] ] = qty 
        else:
            logger.error( 'No Exposure for %s - an error unless this is the first time we run this strategy!' % str( stratAlias ) )
        
        currPort *= shareRatio
            
        winston.addKey( 
            mode=mode, strategyName=stratName, calibDate=tradeDate, 
            key='CurrPort', val=currPort, 
            override=override )
        
        winston.addKey( 
            mode=mode, strategyName=stratName, calibDate=tradeDate, 
            key='SODPort', val=currPort, 
            override=override )

        key     = 'restricted-notrade'
        default = { 'NoOpenShort':set(),'NoCloseSell':set(), 'NoOpenLong':set(), 'NoCloseLong':set() }
        if not winston.hasKey( mode=mode, strategyName=stratName, calibDate=tradeDate, key=key ):
            winston.addKey( 
                mode=mode, strategyName=stratName, calibDate=tradeDate, 
                key=key, val=default, 
                override=override )
            logger.error('--> KEY %s is ABSENT. Creating an empty set' % key )
        else:
            logger.debug('found %s.' % key )

    fExp, sExp = _sodExposure( override=override, tradarType=tradarType, debug=debug )
    
    with twkcx.Tweaks( run_tag = str( tradeDate ) ):
        winston.storeInitialStrategyExposure( sExp, debug=True, override=override )
        winston.storeInitialExposure( fExp, debug=True, override=override )
        winston.storeInitialPrice( nPrice, debug=True, override=override )
        winston.storeInitialMIDS( mids, debug=True, override=override )
    
def _sodExposure( tradarType='tradar-eod', override=False, debug=False ):

    import meadow.strategy.repository as stratrep
    stratrep.init()
    
    sExp        = []
    fExp        = []
    strats      = winston.getModels( debug=True )
    tradeDate   = twkval.getenv( 'run_tradeDate', throwIfNone=True )
    
    iExp, _iPrice, mid2symbol, _blncSheet = trul.initialPos_parse( tradarType )

    mids        = mid2symbol.keys()
    _mids, shareRatio, _priceRatio = posmng.eod2sod( mids, len( mids ) * [1.], len( mids ) * [1.], tradeDate )
    mid2shareRatio = dict( ( mid, r ) for ( mid, r ) in zip( mids, shareRatio ) )  

    '''
    EQUS
            ('Equity', 1000, 2)
            ('Equity', 1006, 2)
            ('Equity', 1007, 579)
            ('Equity', 1011, 20)
    '''

    for stratName in strats:
        _stratInst, params = stratrep.getStrategy( endDate=tradeDate, strategyName=stratName )
        stratAlias = alut.stratAlias( stratName )
        
        execSchema  = params[ 'Execution' ][ 'AllocationSchema' ]
        
        if stratAlias not in iExp:
            logger.error( 'No Exposure for %s - an error unless this is the first time we run this strategy!' % str( stratAlias ) )
            continue
        
        # ('Equity', 1000, 2)
        for ( _secType, mid, qty ) in iExp[ stratAlias ]:
            # ( 'SWAP', 'BARC'    )
            
            qty *= mid2shareRatio[ mid ]
            
            keys = alut.allocKeys( execSchema )
            for key in keys:
                ratio   = alut.allocRatio( execSchema, key )
                row     = ( key, mid,  qty * ratio  )
                fExp.append( row )
                
                row     = ( stratName, key, mid,  qty * ratio  )
                sExp.append( row )
                if debug:
                    logger.debug( 'iExp: %s' % str( row ) )
    return fExp, sExp

def _sodExposureByStrat( tradarType='tradar-eod', override=False, debug=False ):

    import meadow.strategy.repository as stratrep
    stratrep.init()
    
    fExp        = {}
    strats      = winston.getModels( debug=True )
    tradeDate   = twkval.getenv( 'run_tradeDate', throwIfNone=True )
    
    iExp, _iPrice, _mid2symbol, _blncSheet = trul.initialPos_parse( tradarType )

    mids        = _mid2symbol.keys()    
    _mids, shareRatio, _priceRatio = posmng.eod2sod( mids, len( mids ) * [1.], len( mids ) * [1.], tradeDate, throwIfBad=False )
    mid2shareRatio = dict( ( mid, r ) for ( mid, r ) in zip( mids, shareRatio ) )  

    '''
    EQUS
            ('Equity', 1000, 2)
            ('Equity', 1006, 2)
            ('Equity', 1007, 579)
            ('Equity', 1011, 20)
    '''

    for stratName in strats:
        _stratInst, params = stratrep.getStrategy( endDate=tradeDate, strategyName=stratName )
        stratAlias = alut.stratAlias( stratName )
        fExp[ stratAlias ] = []
        
        execSchema  = params[ 'Execution' ][ 'AllocationSchema' ]
        
        if stratAlias not in iExp:
            logger.error( 'No Exposure for %s - an error unless this is the first time we run this strategy!' % str( stratAlias ) )
            continue
        
        # ('Equity', 1000, 2)
        for ( _secType, mid, qty ) in iExp[ stratAlias ]:
            # ( 'SWAP', 'BARC'    )
            
            qty *= mid2shareRatio[ mid ]
            
            keys = alut.allocKeys( execSchema )
            for key in keys:
                ratio   = alut.allocRatio( execSchema, key )
                row     = ( key, mid,  qty * ratio  )
                fExp[ stratAlias ].append( row )
                if debug:
                    logger.debug( 'iExp: %s %s' % ( stratAlias, str( row ) ) )
    return fExp

def _sodPrice( tradarType='tradar-eod', override=False, debug=True ):    
    tradeDate   = twkval.getenv( 'run_tradeDate', throwIfNone=True )
    _iExp, iPrice, mid2symbol, _blncSheet = trul.initialPos_parse( tradarType )
    mids = mid2symbol.keys()
    
    _mids, _shareRatio, priceRatio = posmng.eod2sod( mids, len( mids ) * [1.], len( mids ) * [1.], tradeDate )
    mid2priceRatio = dict( ( mid, r ) for ( mid, r ) in zip( mids, priceRatio ) )  
    
    adjustedPrices  = dict( ( mid, iPrice[ mid ] * mid2priceRatio[ mid ] ) for mid in mids if mid in iPrice )
    return adjustedPrices
