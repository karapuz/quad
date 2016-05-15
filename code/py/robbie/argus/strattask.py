import numpy
import pprint
import traceback
import datetime

import meadow.tweak.value as twkval
import meadow.tweak.util as twkutil
import meadow.tweak.context as twkcx

# import meadow.lib.io as io
import meadow.sim.util as simutil
import meadow.lib.calendar as cal
import meadow.argus.task as argTask
import meadow.lib.winston as winston
import meadow.argus.util as argusutil
import meadow.lib.report as libreport
from   meadow.lib.logging import logger
import meadow.lib.debugging as debugging

import meadow.lib.datetime_util as dut
import meadow.argus.bbgtask as bbgtask 
import meadow.argus.taskenv as taskenv
import meadow.argus.exectask as exectask  
# global system state per strategy
_systemState = {}

def setStateByStrategyKey( stratName, keyName, keyVal ):
    global _systemState
    if stratName not in _systemState:
        _systemState[ stratName ] = {}
    _systemState[ stratName ][ keyName ] = keyVal

def getStateByStrategyKey( stratName, keyName ):
    global _systemState
    if stratName not in _systemState:
        raise ValueError( 'Do not have %s %s!' % ( str( stratName ) , str ( keyName ) ) )
    return _systemState[ stratName ][ keyName ]

def getStrategyState( stratName ):
    if stratName not in _systemState:
        raise ValueError( 'Do not have %s' % str( stratName ) )
    
    return _systemState[ stratName ]
     
def updateCurrPort( orderManager, stratName, cachedCalib, relations, tradeDate, productType ):
    portSymbols = cachedCalib[ 'PortSymbols' ]
        
    exposure    = orderManager.expByStrat( stratName=stratName, productType=productType )
    realized    = exposure[ 'realized'  ]
    
    # logger.debug( 'portSymbols  = %s' % str( portSymbols ) )
    logger.debug( 'realized     = %s' % str( realized ) )
    logger.debug( 'len CurrPort=%s' % len( cachedCalib[ 'CurrPort'   ] ) )
    
    # currPort    = cachedCalib[ 'CurrPort' ]
    addition    = numpy.zeros( len( portSymbols ) )
    for six, sym in enumerate( portSymbols ):
        if sym in realized:
            addition[ six ] = realized[ sym ]

    if getStateByStrategyKey( stratName=stratName, keyName='FirstWave' ):
        # 1. store all exposure we recived thus far for this strategy
        # 2. reset SOD to permanently include it
        #
        externalExposure = addition.copy()
        cachedCalib[ 'SODPort' ] += externalExposure
        argusutil.storeInternal( stratName=stratName, section='execution', name='external_exposure', val=externalExposure )
        setStateByStrategyKey( stratName=stratName, keyName='ExternalExposure', keyVal=externalExposure )
    else:
        externalExposure = getStateByStrategyKey( stratName=stratName, keyName='ExternalExposure'  )
         
    # cachedCalib[ 'CurrPort' ] += addition
    # logger.debug( 'updateCurrPort: CurrPort=%s' % ( str( cachedCalib[ 'CurrPort' ].tolist() ) ) )
    # logger.debug( 'updateCurrPort: SODPort=%s' % ( str( cachedCalib[ 'SODPort' ].tolist() ) ) )
    
    cachedCalib[ 'CurrPort' ] = cachedCalib[ 'SODPort' ] + addition - externalExposure
    
    argusutil.storeInternal( stratName=stratName, section='execution', name='sod_port', val=cachedCalib[ 'SODPort' ] )
    argusutil.storeInternal( stratName=stratName, section='execution', name='curr_port', val=cachedCalib[ 'CurrPort' ] )
    argusutil.storeInternal( stratName=stratName, section='execution', name='addition', val=addition )

def prettyPring( cachedCalib ):
    logger.debug( 'prettyPring ------------------ ' )
    for k in ( 'LCost', 'RiskLambda' ):
        logger.debug( '%s = %s' % ( k, str( cachedCalib[ k ] ) ) )

def applyUpdateAndTrade( blockType, blockName, stratInst, stratName, tradeDate, calibParams, calibData, tradeParams, execParams, spParams ):
    logger.regLogical( logical=stratName )
    logger.debug( 'applyUpdateAndTrade: %s' % str( ( blockType, blockName, stratName, tradeDate ) ) )

    runVar    = ( stratName, 'running' )
    if taskenv.objExists('env', runVar ):
        val = taskenv.getObj('env', runVar )
        logger.error( 'applyUpdateAndTrade: still computing %s' % str( val ) )
        return
    
    taskenv.setObj('env', runVar,  ( blockType, blockName, stratName, tradeDate ) )
    
    ret = _applyUpdateAndTrade( 
            blockType   = blockType, 
            blockName   = blockName, 
            stratInst   = stratInst, 
            stratName   = stratName, 
            tradeDate   = tradeDate, 
            calibParams = calibParams, 
            calibData   = calibData, 
            tradeParams = tradeParams, 
            execParams  = execParams, 
            spParams    = spParams )
    
    taskenv.delObj('env', runVar )
    
    return ret

def _applyUpdateAndTrade( blockType, blockName, stratInst, stratName, tradeDate, calibParams, calibData, tradeParams, execParams, spParams ):
    ''' apply update and trade '''
    logger.regLogical( logical=stratName )
    logger.debug( 'applyUpdateAndTrade: %s' % str( ( blockType, blockName, stratName, tradeDate ) ) )
    
    opMode          = twkval.getenv( 'run_mode' )
    prevCalibDate   = cal.bizday( tradeDate, '-1b' )    

    cachedCalibsVar = ( stratName, 'CachedCalibs')
    
    if taskenv.objExists('env', cachedCalibsVar ):
        cachedCalib  = taskenv.getObj( 'env',  cachedCalibsVar  )
        logger.debug( 'applyUpdateAndTrade: reuse %s id=%s' % ( str( cachedCalibsVar ), id( cachedCalibsVar ) ) )
    else:
        # needs today's stored calibs
        cachedCalib = winston.loadCached(
            mode            = opMode, 
            strategyName    = stratName, 
            calibDate       = tradeDate, 
            prevCalibDate   = prevCalibDate,
            dataName        = 'CachedCalibs' )
    
        taskenv.setObj( 'env',  cachedCalibsVar, cachedCalib )
        logger.debug( 'applyUpdateAndTrade: load into %s id=%s' % ( str( cachedCalibsVar ), id( cachedCalibsVar ) ) )

    marketData  = taskenv.getObj( 'env', 'marketData'       )
    orderManager= taskenv.getObj( 'env', 'orderManager'     )
    orderQueue  = taskenv.getObj( 'env', 'orderQueue'       )
    relations   = taskenv.getObj( 'env', 'relations'        )

    productType = execParams[ 'ProductType' ]
    
    updateCurrPort( 
        orderManager    = orderManager, 
        stratName       = stratName, 
        cachedCalib     = cachedCalib, 
        relations       = relations, 
        tradeDate       = tradeDate, productType=productType )
    
    symbols, closePrice = bbgtask.getMarketDataSlice( marketData=marketData, typeName='close', fieldName='price' )
        
    block       = ( blockType, blockName )
    schedule    = ( ( blockType, blockName, '__EMPTY__' ), )
    lastSlice = { 
            block : { 
                'adjclose': closePrice,
                'close'   : closePrice,
                'symbols' : symbols,
            },
    }

    logger.debug( 'applyUpdateAndTrade closePrice len=%s' % len( closePrice ) )

    updatedCalibData = simutil.amendCalibWithLatest( 
        schedule=schedule, tradeDate=tradeDate, lastSlice=lastSlice, cachedCalib=cachedCalib, 
        calibData=calibData
    )

    logger.debug( 'applyUpdateAndTrade: updatedCalibData.keys=%s' % str( updatedCalibData.keys() ) )

    systemState = getStrategyState( stratName )

    cachedCalib, sharesInfo = stratInst.calibrate( 
                                    blockName   = block, 
                                    params      = calibParams, 
                                    spparams    = spParams, 
                                    calibData   = updatedCalibData, 
                                    cachedCalib = cachedCalib, 
                                    auxParams   = { 'dates': [ tradeDate ], 'TradeDate': tradeDate }, 
                                    tradeParams = tradeParams,
                                    systemState = systemState )
    
    logger.debug( 'applyUpdateAndTrade: sharesInfo=%s' % str( sum( sharesInfo[ 'TradeShares' ] != 0 ) ) )

    # for trade specs
    # algoType, targetTime, targetStep = 'TWLR_TWAP_MV', 45., 1.
    algoType, targetTime, targetStep = 'TWLR_TWAP_MV_TE', 57., 1.
    
    algoInfo    = exectask.formAlgoInfo(
                    algoType    = algoType,
                    targetTime  = targetTime,
                    targetStep  = targetStep )    
    execSchema  = execParams[ 'AllocationSchema' ]
    tradeSpecs  = exectask.generateSpecs( 
                    stratName   = stratName, 
                    algoInfo    = algoInfo, 
                    sharesInfo  = sharesInfo, 
                    tradeDate   = tradeDate, 
                    execSchema  = execSchema )

    argusutil.storeInternal( stratName=stratName, section='execution', name='shares_info', 
                             val=sharesInfo )
    argusutil.storeInternal( stratName=stratName, section='execution', name='symbols_and_prices', 
                             val=( numpy.array( symbols ), numpy.array( closePrice ) ) )

    setStateByStrategyKey( stratName=stratName, keyName='FirstWave', keyVal=False )
    
    logger.debug( 'applyUpdateAndTrade: -------------------> Done' )
    
    return exectask.generateOrders( orderManager, orderQueue, tradeSpecs )

def tradeThroughStandalone( stratName, sharesInfo, tradeDate, algoSpecs ):
    import meadow.strategy.repository as strategyrep
    
    endDate = twkval.getenv( 'run_tag' )
    _instance, params = strategyrep.getStrategy( endDate=endDate, strategyName=stratName )
    
    execParams  = params[ 'Execution' ]

    orderManager= taskenv.getObj( 'env', 'orderManager'     )
    orderQueue  = taskenv.getObj( 'env', 'orderQueue'       )

    # algoType, targetTime, targetStep = 'TWLR_TWAP_MV_TE', 2*57., 5.
    algoType, targetTime, targetStep = algoSpecs
    
    algoInfo    = exectask.formAlgoInfo(
                    algoType    = algoType,
                    targetTime  = targetTime,
                    targetStep  = targetStep )    

    execSchema  = execParams[ 'AllocationSchema' ]
    
    tradeSpecs  = exectask.generateSpecs( 
                    stratName   = stratName, 
                    algoInfo    = algoInfo, 
                    sharesInfo  = sharesInfo, 
                    tradeDate   = tradeDate, 
                    execSchema  = execSchema )

    argusutil.storeInternal( stratName=stratName, section='execution-standalone', name='shares_info', 
                             val=sharesInfo )

    logger.debug( 'tradeThroughStandalone: tradeSpecs %s' % str( tradeSpecs ) )
    
    return exectask.generateOrders( orderManager, orderQueue, tradeSpecs )

def runStrategy( orderQueue, task, tradeDate, flag ):
    
    def _run():
        stratName   = task[ 'StratName'     ] 
        stratInst   = task[ 'StratInst'     ]     
        params      = task[ 'Params'        ] 
        specProc    = task[ 'SpecProcData'  ] 
        _timeSecs   = task[ 'Time'          ] 
        block       = task[ 'Block'         ]

        ( blockType, blockName ) = block
        
        tradeParams = params[ 'TradeParams' ]
        calibParams = params[ 'CalibParams' ]
        execParams  = params[ 'Execution' ]
        spParams    = params[ 'SpecialProcessing' ]
        
        tweaks      = taskenv.getObj( 'env', 'stratTweaks' )
        logger.debug( '%s %s tweaks=%s' % ( stratName, str( block ), str( tweaks ) ) )

        with twkcx.Tweaks( **tweaks ):        
            twkutil.showProdVars()

            applyUpdateAndTrade( 
                    blockType   = blockType, 
                    blockName   = blockName, 
                    stratInst   = stratInst, 
                    stratName   = stratName, 
                    tradeDate   = tradeDate,
                    calibParams = calibParams,
                    calibData   = specProc,
                    tradeParams = tradeParams,
                    execParams  = execParams,
                    spParams    = spParams,
                    )

    def run_():
        try:
            _run()
        except:
            logger.error( 'FAIL: runStrategy._run' )
            logger.error( traceback.format_exc() )
            
    return run_

class StratTask( argTask.Task ):
    
    def __init__(self, orderQueue, task, tradeDate ):
        super( StratTask, self ).__init__()
        
        self._orderQueue= orderQueue
        
        self._task      = task
        self._flag      = argusutil.Flag( True )
        
        self._env       = twkval.getenv( 'run_env' )
        self._run       = runStrategy( orderQueue=orderQueue, task=task, tradeDate=tradeDate, flag=self._flag )
                
        logger.debug('StratTask env=%s %s' % ( self._env, 'init' ) )

    def stop(self, tag, logger ):
        self._flag.cont = False
        logger.debug('StratTask %s stop' % tag )
    
    def start(self, tag, logger ):
        logger.debug('StratTask tag=%s %s' % ( tag, 'start' ) )
        self._flag.cont = True
        self._run()

class ManagementTask( argTask.Task ):
    
    def __init__(self, orderQueue, task, tradeDate ):
        super( ManagementTask, self ).__init__()
        self._task      = task
        self._tradeDate = tradeDate
        logger.debug('ManagementTask %s %s' % ( tradeDate, 'init' ) )

    def stop(self, tag, logger ):
        logger.debug('ManagementTask %s stop' % tag )
    
    def start(self, tag, logger ):
        logger.debug('ManagementTask tag=%s %s' % ( tag, 'start' ) )
        opMode          = 'trade-prod'
        strategyName    = self._task[ 'StratName'     ]
        
        cachedCalibsVar = ( strategyName, 'CachedCalibs' )
        cachedCalib     = taskenv.getObj( 'env',  cachedCalibsVar )
        
        winston.saveCached( 
                mode         = opMode, 
                strategyName = strategyName, 
                calibDate    = self._tradeDate, 
                dataName     = 'CachedCalibs', 
                dataVals     = cachedCalib )
        
        # libreport.reportAndKill(txt='Shutting Down', subject='Argus is shut-down', sendFrom='argus', sendTo='ipresman' )

class ReportKillTask( argTask.Task ):
    
    def __init__(self, orderQueue, task, tradeDate ):
        super( ReportKillTask, self ).__init__()
        self._task      = task
        self._tradeDate = tradeDate
        logger.debug('ReportKillTask %s %s' % ( tradeDate, 'init' ) )

    def stop(self, tag, logger ):
        logger.debug('ReportKillTask %s stop' % tag )
    
    def start(self, tag, logger ):
        logger.debug('ReportKillTask tag=%s %s' % ( tag, 'start' ) )

        libreport.reportAndKill(txt='Shutting Down', subject='Argus is shut-down', sendFrom='argus', sendTo='ipresman' )

class TestExecTimes( object ):
    
    def __init__(self, schedType, N=100 ):
        
        self._schedType = schedType
        self._count     = 0
        self._max       = N
        now             = datetime.datetime.now()
        
        if schedType == 'now+1m':
            delta = datetime.timedelta( 0, 60 )
        elif schedType == 'now+2m':
            delta = datetime.timedelta( 0, 2*60 )
        elif schedType == 'now+3m':
            delta = datetime.timedelta( 0, 3*60 )
        elif schedType == 'now+1s':
            delta = datetime.timedelta( 0, 1 )
        elif schedType == 'now+5s':
            delta = datetime.timedelta( 0, 5 )
        else:
            raise ValueError( 'Unknown schedType = %s' % str( schedType ) )
        
        self._now       = now
        self._delta     = delta

    def reset( self ):        
        self._count     = 0
        
    def hasMore(self):        
        return self._schedType and self._count < self._max

    def isValid(self):        
        return self.hasMore()

    def next(self):
        if self._count >= self._max:
            raise StopIteration()
        
        self._count += 1
        
        now_        = self._now + self._delta * self._count    
        timeSecs    = dut.toTimeSec( now_.time() )
        timeStr     = dut.timeStr( now_.time() )
        return timeSecs, timeStr
    
def initStrategy( endDate, tradeDate ):
    ''' load and initialize the strategies '''

    import meadow.strategy.schedule as stratsched
    import meadow.strategy.repository as strategyrep
    import meadow.sim.dailyDriverMultiBlock as driver    

    strategyrep.init()

    stratNames  = winston.getModels( debug=True )
    mode        = 'trade-prod'
    strats      = {}

    tweaks      = { 'debug_level':debugging.LEVEL_LOW, 'run_mode':mode, 'run_tradeDate':tradeDate } 
    taskenv.setObj( 'env', 'stratTweaks', tweaks )

    for stratName in stratNames:
        
        # need to temporarily re-register main thread
        logger.regLogical( logical=stratName )
        strategyInstance, origParams = strategyrep.getStrategy( endDate=endDate, strategyName=stratName )
        
        with twkcx.Tweaks( **tweaks ):        
            twkutil.showProdVars()            
            stratInst, specProcData  = driver.run(
                                                strategyInstance = strategyInstance, 
                                                params           = origParams, 
                                                fullName         = stratName )        
        strats[ stratName ] = {
            'StratName'    : stratName,
            'StratInst'    : stratInst,
            'Params'       : origParams,
            'SpecProcData' : specProcData,
        }

    schedType   = twkval.getenv( 'argus_schedule' )
    if schedType:
        execTimes   = TestExecTimes( schedType=schedType )
                
    tasks       = []
    maxTimeSecs = 0
    for stratName in stratNames:
        logger.regLogical( logical=stratName )
        
        params      = strats[ stratName ][ 'Params'         ]
        specProc    = strats[ stratName ][ 'SpecProcData'   ]
        stratInst   = strats[ stratName ][ 'StratInst'      ]
        schedule    = params[ 'GetData' ][ 'Schedule']
    
        logger.debug( 'initStrategy: specProc.keys: %s' % pprint.pformat(object=specProc.keys() ) )
    
        if schedType:
            execTimes.reset()
                
        for blockType, blockName, blockSpecs in schedule:
            
            if blockType not in ( 'Update', ):
                logger.debug( 'Strat: %12s skips %12s' % ( stratName, str( blockSpecs ) ) )
                continue
            
            if blockType in ( 'Update' ):
                if schedType and execTimes.isValid():
                    timeSecs, timeStr = execTimes.next()
                else:
                    timeStr = stratsched.getSliceTime( blockSpecs, 'asStr' )
                    timeSecs= stratsched.getSliceTime( blockSpecs, 'asSec' )

            logger.debug( 'Strat: %12s set %12s to %12s' % ( stratName, blockType, timeStr ) )
                        
            setStateByStrategyKey( stratName, 'FirstWave', True )            
            
            tasks.append( {
                'StratName'     : stratName,
                'StratInst'     : stratInst,
                'Params'        : params,
                'SpecProcData'  : specProc,
                
                'Time'          : timeSecs,
                'SchedLine'     : blockSpecs,
                'Block'         : ( blockType, blockName ),
                'Schedule'      : schedule,
            } )

        if isinstance( timeSecs, datetime.time ):
            timeSecs = datetime.time( 16, 4 )
        else:
            timeSecs += 5*60
            maxTimeSecs = max( maxTimeSecs, timeSecs )
            
        tasks.append( {
            'StratName'     : stratName,
            'StratInst'     : stratInst,
            'Params'        : params,
            'SpecProcData'  : specProc,
            
            'Time'          : timeSecs,
            'SchedLine'     : blockSpecs,
            'Block'         : ('Management', ( 'Store', 'CachedCalibs') ),
            'Schedule'      : schedule,
        } )

    if isinstance( timeSecs, datetime.time ):
        timeSecs = datetime.time( 16, 9 )
    else:
        timeSecs = maxTimeSecs + 5*60
        
    tasks.append( {
        'StratName'     : None,
        'StratInst'     : stratInst,
        'Params'        : params,
        'SpecProcData'  : specProc,
        
        'Time'          : timeSecs,
        'SchedLine'     : blockSpecs,
        'Block'         : ('ReportKill', ( None, None ) ),
        'Schedule'      : schedule,
    } )
            
    logger.regLogical( logical=None )
    return tasks

def schedStrats( orderQueue, server, tasks, tradeDate ):
    import meadow.argus.taskrepository as taskrep
    
    for task in tasks:
        stratName   = task[ 'StratName'     ]
        timeSecs    = task[ 'Time'          ] 
        block       = task[ 'Block'         ]     

        ( blockType, blockName ) = block

        schedName       = stratName
        taskType, env   = ( stratName, blockType, blockName ), 'trade-prod'
        taskPath        = ( taskType, env )
        
        if blockType   == 'Management':
            taskObj     = ManagementTask( orderQueue=orderQueue, task=task, tradeDate=tradeDate )
            
        elif blockType == 'ReportKill':
            taskObj     = ReportKillTask( orderQueue=orderQueue, task=task, tradeDate=tradeDate )
            
        else:
            taskObj     = StratTask( orderQueue=orderQueue, task=task, tradeDate=tradeDate )
        
        taskrep.setStartStopSched( schedName=schedName, startTime=timeSecs )
        taskrep.setTask( taskPath=taskPath, taskObj=taskObj )
        
        server.startTask( env=env, taskType=taskType, schedName=schedName )

def startStrat( server ):
    try:
        return _startStrat( server )
    except:
        logger.error( 'FAIL: startStrat._startStrat' )
        logger.error( traceback.format_exc() )

def _startStrat( server ):
    ''' schedule all steps of the strategy '''

    orderQueue  = taskenv.getObj( 'env', 'orderQueue' )
    today       = cal.today()
    
    endDate     = twkval.getenv( 'run_tag' ) or today 
    tradeDate   = twkval.getenv( 'run_tradeDate' ) or today

    endDate     = int( endDate )
    tradeDate   = int( tradeDate )
    tasks       = initStrategy( endDate=endDate, tradeDate=tradeDate )

    logger.debug( 'starting trade-prod endDate=%s tradeDate=%s' % ( endDate, tradeDate ) )        
    schedStrats( orderQueue=orderQueue, server=server, tasks=tasks, tradeDate=tradeDate )

    return True, ''
