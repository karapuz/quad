'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : strategy.base module
'''

from   robbie.util.logging import logger
import robbie.strategy.base_trade as base_trade

class BaseStrategyMultiBlock( object ):
    
    def __init__(self):
        self._debug = False
        
    def getData( self, modelName, params, includeDivs = False ):
        ''' '''
        
        import robbie.strategy.base_getdata as base_getdata
        scheduleNames = params['Schedule']
                
        ret = base_getdata.sa_getMergedMultiBlock(
            modelName     = modelName, 
            params        = params, 
            debug         = False, 
            scheduleNames = scheduleNames, 
            includeDivs   = includeDivs )
                
        ret[ 'Schedule' ] = scheduleNames
        return ret 
    
    def specialProcessing( self, modelName, params, origData, stratSymbols ):
        ''' '''
        
        import robbie.strategy.base_specialprocessing as base_sp
        
        spData = {}
        for blockName, blockVals in origData.iteritems():
            blockType = blockName[0]
            if blockType in ( 'Calib', 'Trade', 'Update', 'Mrk2Mkt' ): 
                spData[ blockName ] = base_sp.sa_specialProcessing( blockName=blockName, params=params, origData=blockVals, stratSymbols=stratSymbols )
                spData[ blockName ][ 'symbology' ] = blockVals[ 'symbology' ]
            else:
                logger.debug( '%s is not special-processed' % str( blockName ) )
             
        spData[ 'Schedule' ] = origData[ 'Schedule' ]
        return spData
 
    def incrSpecialProcessing( self, blockName, params, calibData, cachedCalib ):
        ''' default incremental special processing '''
        return cachedCalib

    def updateCachedCalibsForIncrSpecialProcessing(self, params, calibData, cachedCalib ): 
        ''' update data for the incremental special processing '''
        return cachedCalib
       
    def calibrate( self, blockName, params, spparams, calibData, cachedCalib, auxParams, tradeParams, systemState ):
        pass

    def trade( self, tradeDate, tradeParams, blockName, specProcData, calibData, sharesInfo, multiPeriodTrades ):
        return base_trade.sa_tradeWithTransactionCostsByBasisPointsMultiBlock( tradeDate=tradeDate, tradeParams=tradeParams, blockName=blockName, specProcData=specProcData, calibData=calibData, sharesInfo=sharesInfo, multiPeriodTrades=multiPeriodTrades )

    def shouldProcess( self, opMode, calibIx, dates ):
        ''' by default, always process all dates for all modes '''
        return True

    def removeDelistedSymbols( self, tradeDate, cachedCalib ):
        ''' should remove de-listed symbols '''
        return cachedCalib

    def initialize( self, opMode, specProcData, cachedCalib ):
        pass

    def finalize( self, cachedCalib ):
        pass

    def modeConversion( self, strategyName, cachedCalib, modeFrom, modeTo ):
        ''' will be used to create the zero-day trade-prod cachedCalib '''
        import copy
        return copy.deepcopy( cachedCalib )
