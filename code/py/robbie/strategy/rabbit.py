import numpy
import datetime

from   meadow.lib.logging import logger
import meadow.strategy.base as strat_base
from meadow.lib.symbChangeDB import symbDB
import meadow.strategy.base_util as base_util

class Strategy( strat_base.BaseStrategyMultiBlock ):
                            
    def calibrate( self, blockName, params, calibData, cachedCalib ):
        '''returns amount traded'''
                
        adjprice    = calibData[ blockName ][ 'adjclose'    ]
        volume      = calibData[ blockName ][ 'volume'      ]
        symbols     = calibData[ blockName ][ 'symbols'     ]                
        dates       = calibData[ blockName ][ 'dates'       ]                

        blockType, blockSpecs = blockName

        shares = None
        
        if blockType == 'Calib':
            opType = blockSpecs[0]
            if opType == 'SOD':
                cachedCalib[ 'cov' ] = numpy.cov( adjprice )
                
        elif blockType == 'Update':            
            lastKey, calibKey = blockSpecs
            
            opType = lastKey[0]            
            if opType == 'STS':
                shares = numpy.sign( volume[-1,:] - numpy.mean( volume, 0 ) )
                
            elif opType == 'LTS':
                shares = numpy.sign( volume[-1,:] - numpy.mean( volume, 0 ) )
            
        else:
            raise ValueError( 'Unknown blockType = %s' % str( blockType ) )
        
        if cachedCalib[ 'FirstTime' ] == True:
            logger.debug( 'FirstTime' )            
        
        logger.customWrite( 'internalState', dates[-1], numpy.mean( volume, 0 ) )
        logger.customWrite( 'guys', datetime.datetime.now(), [ numpy.random.randn(), numpy.random.randn() ] )

        sharesInfo = { 
            'TradeSymbols'  : symbols,
            'TradeShares'   : shares,
        }
        return cachedCalib, sharesInfo

    def initialize( self, specProcData, cachedCalib ):
        ''' '''
        calibName   = base_util.checkCalibDatesAndSymbols( specProcData )
        dates       = specProcData[ calibName ][ 'dates'    ]
        symbols     = specProcData[ calibName ][ 'symbols'  ]
        typ         = specProcData[ calibName ][ 'symbology']
            
        if typ == 'MID':
            symbols = [ symbDB.MID2symb( MID, date=int( dates[-1] ) ) for MID in symbols ]
        else:
            raise ValueError( 'Unknown symbology=%s' % typ )
        
        logger.customHeader( 'internalState', symbols )
        logger.customHeader( 'guys', ['Tengjie', 'XuDong'] )
        