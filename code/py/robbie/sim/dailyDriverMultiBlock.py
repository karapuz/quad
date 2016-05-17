''' upper level driver '''

import sys
import numpy

import robbie.util.calendar as cal
import robbie.sim.util as simutil
import robbie.run.mode as run_mode
import robbie.util.fetch as libfetch
import robbie.tweak.value as twkval
import robbie.lib.winston as winston
import robbie.lib.context as context
import robbie.argus.util as argusutil

from   robbie.util.logging import logger
import robbie.util.vendortranslation as vtran
import robbie.strategy.base_util as base_util
import robbie.strategy.signature as signature

def formOldStyleDates( oldOffset, calibDates, tradeDate, tradeDates ):
    if tradeDate not in tradeDates:
        msg = 'tradeDate=%s is not in tradeDates=%s' % ( tradeDate, str( tradeDates ) )
        logger.error( msg )
        raise ValueError( msg )
    
    calibDates  = calibDates[oldOffset: ].tolist()
    tradeDates  = tradeDates[ : tradeDates.index( tradeDate ) + 1 ]
    oldDates    = sorted( set( calibDates + tradeDates ) )
    return oldDates

def run( strategyInstance, params, fullName, verbose=True ):
    from   meadow.lib.symbChangeDB import symbDB
    isDumping = False
    
    # the daily matrices are returned in a dictionary
    strategyName= fullName
    opMode      = twkval.getenv( 'run_mode' )
    tradeDate   = twkval.getenv( 'run_tradeDate' )
    opRegime    = twkval.getenv( 'dev_regime' )

    calibParams = params[ 'CalibParams' ]
    tradeParams = params[ 'TradeParams' ]
    runparams   = params[ 'Run'         ]    
    spParams    = params[ 'SpecialProcessing' ]
    
    step        = runparams[ 'Step'         ]
    calibWindow = runparams[ 'CalibWindow'  ]
    calibOffset = runparams.get( 'CalibOffset', 1 ) # if offset is one, we include today in calibs

    systemState = { }
    
    stratSymbols= None
    loadedCachedCalibs = False
    if run_mode.needsCache( opMode ):

        if opMode in ( 'sim', 'sim-seed'):
            loadCacheDate   = cal.bizday( tradeDate, '-1b' )
            
        elif opMode in( 'sim-prod', 'trade-prod', ):            
            loadCacheDate   = tradeDate
    
        cachedCalib = winston.loadCached(
            mode         = opMode, 
            strategyName = strategyName, 
            calibDate    = tradeDate, 
            prevCalibDate= loadCacheDate,
            dataName     = 'CachedCalibs',
            throw        = False )
        
        if cachedCalib:
            stratSymbols    = cachedCalib[ 'symbols' ]
            loadedCachedCalibs=True
        else:
            stratSymbols    = None

        symbols = stratSymbols

    elif opMode == 'dev':
        cachedCalib = {}

    else:
        raise ValueError( 'Unknown mode=%s' % opMode )
            
    origData = strategyInstance.getData(
                    params[ 'StrategyName'  ],
                    params[ 'GetData'       ] 
                )

    specProcData = strategyInstance.specialProcessing( 
                    params[ 'StrategyName'      ],
                    params[ 'SpecialProcessing' ], 
                    origData, stratSymbols,
                )

    if opRegime == 'specialproc':
        libfetch.dump( ( opMode, strategyName ), specProcData, debug=True )
        raise ValueError('Done!')

    calibName       = base_util.checkDatesAndSymbols( targetType='Calib', specProcData=specProcData )
    if opMode in ( 'sim', 'dev' ):
        symbols     = numpy.array( specProcData[ calibName ][ 'symbols' ] )
        _defaults   = {
            'FirstTime'     : True,
            'symbols'       : numpy.array( symbols ),
            'CurrPort'      : numpy.zeros( len( symbols ) ),
            'SODPort'       : numpy.zeros( len( symbols ) ),
            'restricted-notrade': { 'NoOpenShort':set(),'NoCloseSell':set(), 'NoOpenLong':set(), 'NoCloseLong':set() },
        }
        for key in _defaults:
            if key not in cachedCalib:
                val = _defaults[ key ]
                cachedCalib[ key ] = val
                logger.debug( 'CachedCalibs: updating key=%s to use default %s' % ( key, str( val ) ) )
    
    stratSymbols = stratSymbols if stratSymbols != None else symbols 
    initPosition= cachedCalib[ 'SODPort' ]
    cacheDate   = tradeDate
    calibDates  = specProcData[ calibName  ][ 'dates' ]

    if opMode in ( 'sim', 'dev', 'sim-prod' ):
        updateName  = base_util.checkDatesAndSymbols( targetType='Update', specProcData=specProcData )
        tradeDates  = specProcData[ updateName ][ 'dates' ].tolist()    
    
    dates       = calibDates
    dataLen     = len( dates )
    logger.debug( 'symbols len: %s dates len: %s ' % ( len( symbols ), dataLen ) )
    
    strategyInstance.initialize( opMode, specProcData, cachedCalib )
    
    if opMode == 'trade-prod':
        return strategyInstance, specProcData

    if not run_mode.isValidMode( opMode ):
        raise ValueError( 'Unknown opMode=%s' % opMode)

    oldOffset       = 1 + simutil.findInitOffset( runparams[ 'InitialOffset'], dates )        
    firstCalibDate  = cal.bizday( runparams[ 'InitialOffset'], '-2b' )
    
    if firstCalibDate not in dates:
        msg = 'firstCalibDate=%s not in dates=%s' % ( firstCalibDate, str( dates ) )
        logger.error( msg )
        raise ValueError( msg )
    
    initCalibOffset = 1 + simutil.findInitOffset( firstCalibDate, dates )        
    fullRange       = range( initCalibOffset, len( dates ), step )
    lastIx          = fullRange[-1]

        
    if opMode in (  'sim-seed', 'sim-prod', 'dev', 'sim' ):
        posMonType = twkval.getenv( 'sim_posMon' )
        if posMonType == 'market':
            import meadow.strategy.posmon as posmon
        elif posMonType == 'limit':
            import meadow.strategy.posmon_limitorders as posmon
        else:
            raise ValueError( 'Unknown sim_posMon=%s' % str( posMonType ) )
        
        posMon = posmon.PositionMonitor( 
                        dirName  = logger.dirName(), 
                        symbols  = stratSymbols, 
                        recordPositionHistory = True, 
                        positions = initPosition )        
    
    # endIx - is the Calib block based
    if opMode in ( 'sim-prod', 'sim-seed', 'trade-prod' ):
        
        fullRange = [ lastIx ]
        
        if opMode == 'sim-seed':
            loadCacheDate   = cal.bizday( tradeDate, '-1b' )
            
        elif opMode in( 'sim-prod', 'trade-prod', ):
            
            loadCacheDate   = tradeDate
        else:
            raise ValueError( 'Wrong opMode=%s' % opMode )

        cachedCalib = winston.loadCached(
            mode         = opMode, 
            strategyName = strategyName, 
            calibDate    = tradeDate, 
            prevCalibDate= loadCacheDate,
            dataName     = 'CachedCalibs',
            throw        = False )

        # add model verification exceptions
        vExceptions     = signature._exceptions
        
        vExceptions_    = winston.loadVerificationExceptions( throw=False )                
        if vExceptions_:
            vExceptions.extend( vExceptions_[ strategyName ] )            
        
        logger.debug( 'vExceptions: %s' % str( vExceptions ) )
        
        signature.validate( 
            validationName = ( opMode, strategyName ), 
            cachedCalib     = cachedCalib, 
            signatureName   = 'ModelSignature', 
            params          = params,
            exceptions      = vExceptions )

        assert( cal.bizday( tradeDate, '-1b' ) == dates[ lastIx ] )
                
    elif opMode in ( 'dev', 'sim' ):
        if opMode == 'sim':
            if not cal.bizday( tradeDate, '-2b' ) == dates[ lastIx ]:
                raise AssertionError(  '%s %s' % ( cal.bizday( tradeDate, '-2b' ), dates[ lastIx ] ) )
        
    else:
        raise ValueError( 'Unknown mode = %s' % opMode )

    logger.debug( 'lastDate=%s cacheDate=%s First Calib Offset=(%s,%s) step=%s, dataLen=%s' % ( 
                dates[ lastIx ], cacheDate, initCalibOffset, firstCalibDate, step, dataLen ) 
    )
    
    stepIndex   = 0        
    calibParams[ 'InitialOffset' ] = initCalibOffset

    if isDumping:
        fetchName = ( 
            ( 'type', 'data' ),
            ( 'subtype', 'specProcData' ), 
        )
        if opMode not in (  'sim', 'dev' ):
            logger.error( 'Wrong Mode - can not dump under %s mode' % opMode )
        else:
            libfetch.dump( name=fetchName, obj=specProcData, debug=True )
            sys.exit()

        
    for calibIx in fullRange:
        cacheLoaded     = opMode == 'sim'
        
        systemState[ 'FirstWave' ] = True
        
        mpTrades        = [ ]
        prevCalibDate   = dates[ calibIx-1 ]
        calibDate       = int( dates[ calibIx ] )
        firstStep       = ( stepIndex == 0 )
        schedule        = specProcData[ 'Schedule' ]        
        
        calibData       = simutil.calibDataSliceMultiBlock( 
                            data        = specProcData, 
                            params      = runparams, 
                            calibIx     = calibIx, 
                            calibWindow = calibWindow, 
                            offset      = calibOffset )

        tradeDate_      = cal.nextbizday( calibDate )
        
        if opMode in ( 'sim', 'dev', 'sim-prod' ):
            oldDates = formOldStyleDates( 
                            oldOffset   = oldOffset, 
                            calibDates  = dates, 
                            tradeDate   = tradeDate_, 
                            tradeDates  = tradeDates )
        else:
            oldDates = None

        if opMode == 'sim-prod':
            # prepare keys for current sim prod run
            simutil.reusePrevDayData( 
                opMode       = 'sim-prod', 
                strategyName = strategyName, 
                cachedCalib  = cachedCalib, 
                tradeDate    = tradeDate_, 
                calibDate    = calibDate )
            
        if calibDate != cal.bizday( prevCalibDate, '+1b' ):
            msg = 'gap in dates! %s -> %s' % ( calibDate, prevCalibDate )
            logger.error( msg )
            raise ValueError( msg )
        
        for blockType, blockSpecs, _alias in schedule:
            blockName = ( blockType,  blockSpecs )
            
            if not strategyInstance.shouldProcess( opMode, calibIx, dates ):
                logger.debug( 'shouldNotRun: mode=%s date=%s' % ( opMode, calibDate ))
                continue
            
            if blockType == 'Calib':
                
                if run_mode.modeRunsInCalibBlock( mode=opMode ):

                    if opMode not in ( 'dev', ) and loadedCachedCalibs:
                        if 'NeedDelist' in spParams:
                            if spParams['NeedDelist'][0]:
                                deldate     = cal.bizday(dates[calibIx], '+1b') 
                                cachedCalib = strategyInstance.removeDelistedSymbols( tradeDate=deldate, cachedCalib=cachedCalib )
                                posMon.removeDelistedSymbols( deldate )
                                calibData[blockName] = strategyInstance.removeDelistedSymbolsCD( tradeDate=deldate, calibData=calibData[blockName] ) 
                            else : 
                                cachedCalib = strategyInstance.removeDelistedSymbols( tradeDate=tradeDate, cachedCalib=cachedCalib )
                                posMon.removeDelistedSymbols( tradeDate )

                    if run_mode.needsIncrSpecialProc( opMode ):
                        cachedCalib = strategyInstance.incrSpecialProcessing( 
                            blockName=blockName, params=spParams, calibData=calibData, cachedCalib=cachedCalib 
                        )
                        
                    with context.Timer( 'calib' ) as timerCon:
                         
                        cachedCalib, sharesInfo = strategyInstance.calibrate( 
                            blockName   = blockName, 
                            params      = calibParams,
                            spparams    = spParams, 
                            calibData   = calibData, 
                            cachedCalib = cachedCalib, 
                            auxParams   = { 'dates': oldDates, 'TradeDate': tradeDate_ },
                            tradeParams = tradeParams,
                            systemState = systemState,
                        )
                    
                    if verbose:    
                        logger.debug( '%s [CalibDate] %s' % ( calibDate, timerCon.elapsed() ) )
                    
                    # pure calib should never produce shares info
                    assert( base_util.noShares( sharesInfo ) )

            elif blockType == 'Update':
                # we now see the latest slice - need to amend the calibration                    

                if not run_mode.modeRunsInUpdateBlock( mode=opMode ):
                    continue

                # update needs today's stored calibs
                if not cacheLoaded and run_mode.needsCache( opMode ):
                    cacheLoaded = True
                    cachedCalib = winston.loadCached(
                        mode          = opMode, 
                        strategyName  = strategyName, 
                        calibDate     = tradeDate, 
                        prevCalibDate = loadCacheDate,
                        dataName      = 'CachedCalibs' )

                lastSlice   = simutil.lastDataSliceMultiBlock( 
                    specProcData=specProcData, tradeDate=tradeDate_ 
                )
                
                updatedCalibData   = simutil.amendCalibWithLatest( 
                    schedule=schedule, tradeDate=tradeDate_, lastSlice=lastSlice, cachedCalib=cachedCalib, 
                    calibData=calibData 
                )

                # assert( cachedCalib['symbols'].tolist() == specProcData[ ('Calib', ('SOD', '0'))] ['symbols'] )
                # assert( cachedCalib['symbols'].tolist() == specProcData[ calibName ] ['symbols'] )
                
                if opMode in ( 'dev','sim' ):
                    oldDates = updatedCalibData[ ('Update', (('LTS', '0'), ('SOD', '0'))) ]['dates'].tolist()

                cachedCalib, sharesInfo = strategyInstance.calibrate( 
                    blockName   = blockName, 
                    params      = calibParams, 
                    spparams    = spParams, 
                    calibData   = updatedCalibData,
                    cachedCalib = cachedCalib, 
                    auxParams   = { 'dates': oldDates },
                    tradeParams = tradeParams,
                    systemState = systemState,
                )
                
                if opMode in ( 'sim-prod', 'trad-prod' ):
                    argusutil.storeInternal( stratName=strategyName, section='execution', name='shares_info', val=sharesInfo )
                    argusutil.storeInternal( stratName=strategyName, section='execution', name='symbols_and_prices', val=( symbols, lastSlice ) )

            elif blockType == 'Trade':
                
                if not run_mode.modeRunsInTradeBlock( mode=opMode ):
                    continue
                
                tradedPos   = strategyInstance.trade( 
                    tradeDate   = tradeDate_, 
                    tradeParams = tradeParams, 
                    blockName   = blockName, 
                    specProcData= specProcData, 
                    calibData   = updatedCalibData, 
                    sharesInfo  = sharesInfo, 
                    multiPeriodTrades = mpTrades
                )

                simutil.updatePortfolio( tradedPos, cachedCalib, typ='CurrPort' )                        
                mpTrades.append( tradedPos )
                # change system state to 'not the first wave'
                systemState[ 'FirstWave' ] = False

            elif blockType == 'TradeAndM2MLimits':
                
                if not run_mode.modeRunsInTradeBlock( mode=opMode ):
                    continue
                
                tradedPos   = strategyInstance.tradeLimits(
                    posMon      = posMon,
                    tradeDate   = tradeDate_, 
                    tradeParams = tradeParams, 
                    blockName   = blockName, 
                    specProcData= specProcData, 
                    calibData   = updatedCalibData, 
                    sharesInfo  = sharesInfo, 
                    multiPeriodTrades = mpTrades
                )

                simutil.updatePortfolio( tradedPos, cachedCalib, typ='CurrPort' )                        
                mpTrades.append( tradedPos )
                # change system state to 'not the first wave'
                systemState[ 'FirstWave' ] = False

            elif blockType == 'Mrk2Mkt':
                
                if not run_mode.modeRunsInMrk2MktBlock( mode=opMode ):
                    continue
                    
                symbols, shares, _avgprices, prices, tCosts, sCosts, totalShareInfo  = simutil.getAvgTradePrice( mpTrades )
                costs =  tCosts + sCosts
                
                simutil.updatePortfolio( totalShareInfo, cachedCalib, typ='SODPort' )

                if opMode in ( 'sim-prod', 'sim', 'dev' ):
                    posMon.addShares( date=tradeDate_, symbols=symbols, shares=shares, prices=prices, costs=costs )
                
                    mrktSlice   = simutil.lastDataSliceMultiBlock( 
                        specProcData=specProcData, tradeDate=tradeDate_ 
                    )
                    marketPrice = simutil.getMarketPrice( symbols, mrktSlice[ blockName ] )
                    posMon.doMrk2Mkt(date=tradeDate_, marketPrice=marketPrice, marketSymbols=symbols, costs=costs )
                    if 'Mrk2Mkt_TJ' in params and params[ 'Mrk2Mkt_TJ' ]:
                        #wave1Price  = specProcData[('Update', (('LTS', '0'), ('SOD', '0')))]['adjclose'][-2,:] #yesterday price at 3:51
                        eodPrice    = specProcData[('Mrk2Mkt', (('EOD', '0'),))]['adjclose'][-1,:]              # today eod price
                        eodpPrice    = specProcData[('Mrk2Mkt', (('EOD', '0'),))]['adjclose'][-2,:]             # yesterday eod price
                        posMon.doMrk2Mkt_TJ(date=tradeDate_, eodPrice=eodPrice, eodpPrice=eodpPrice, marketSymbols=symbols, costs=costs, shares=shares )

                    
            else:
                raise ValueError( 'Unknown data block type = %s in %s' % ( str( blockType ), str( blockName ) ) )

        stepIndex += 1        
        if firstStep:                
            cachedCalib[  'FirstTime' ] = False

    #
    # we always save the last clean sim/sim-seed
    # we need it as our seed for the next sim-seed/sim-prod/trade-prod
    #
    if opMode in ( 'sim', 'sim-seed', 'sim-prod' ):
        
        if opMode in ( 'sim' , 'sim-seed' ):
            cachedCalib = strategyInstance.updateCachedCalibsForIncrSpecialProcessing( 
                params=calibParams, calibData=calibData, cachedCalib=cachedCalib 
            ) 

        portMIDs        = cachedCalib[ 'symbols' ]
        
        portSymbols     = [ vtran.meadowSymb2BloombergSymb( 
                                symbStr=symbDB.MID2symb( mid, tradeDate ), includeCountry=False, includeEquity=False ) 
                                    for mid in portMIDs ]
        
        cachedCalib[ 'PortSymbols'      ] = portSymbols
        cachedCalib[ 'ModelSignature'   ] = params

        if opMode == 'sim':
            targetMode = 'zero-trade-prod'
            newCachedCalib  = strategyInstance.modeConversion( strategyName, cachedCalib, 'sim', targetMode )
            
            winston.saveCached( 
                    mode         = 'sim', 
                    strategyName = strategyName, 
                    calibDate    = cacheDate, 
                    dataName     = 'CachedCalibs', 
                    dataVals     = newCachedCalib )

        else:
            winston.saveCached( 
                    mode         = opMode, 
                    strategyName = strategyName, 
                    calibDate    = cacheDate, 
                    dataName     = 'CachedCalibs', 
                    dataVals     = cachedCalib )


    if opMode == 'sim-prod':
        winston.saveCached( 
                mode         = opMode, 
                strategyName = strategyName, 
                calibDate    = cacheDate, 
                dataName     = 'mpTrades', 
                dataVals     = mpTrades )
        
    strategyInstance.finalize( cachedCalib )            

    if opMode in ( 'sim-prod', 'sim', 'dev' ):
        return strategyInstance, cachedCalib, posMon
    else:
        return strategyInstance, cachedCalib, None
