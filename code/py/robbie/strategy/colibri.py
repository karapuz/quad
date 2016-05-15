import numpy

import meadow.lib.context as cx
# import meadow.tweak.value as twkval
import meadow.strategy.base as strat_base
import meadow.strategy.colibri_util as colut
import meadow.strategy.colibri_calibrate as colcal

from   meadow.lib.logging import logger

class Strategy( strat_base.BaseStrategyMultiBlock ):
    
    def initialize( self, opMode, specProcData, cachedCalib ):
        cachedCalib[ 'BoundObjects' ] = []

    def tradeLimits( self, posMon, tradeDate, tradeParams, blockName, specProcData, calibData, sharesInfo, multiPeriodTrades ):
        sharesInfos = sharesInfo[ 'SliceTradeShares' ]
        symbols     = sharesInfo[ 'TradeSymbols' ]
        
        pos         = numpy.zeros( len( symbols ) )
        totalCosts  = numpy.zeros( len( symbols ) )
        
        for shareSlice in sharesInfos:
            assert numpy.all( shareSlice[ 'symbols' ] == symbols )
            qty     = shareSlice[ 'qty' ]
            prices  = shareSlice[ 'price' ]
            shares  = qty
            costs   = numpy.abs( qty ) * .005            
            if not sum( numpy.abs( shares ) ):
                continue
        
            totalCosts += costs    
            pos += qty
            posMon.addShares( date=tradeDate, symbols=symbols, shares=shares, prices=prices, costs=costs )
        
        tradedPos = { 
            'TradeShares'       : pos,
            'TradeSymbols'      : symbols,
            'TransactionCosts'  : totalCosts, 
        }

        return tradedPos

    def calibrate( self, blockName, params, spparams, calibData, cachedCalib, auxParams, tradeParams, systemState ):
        '''
        returns amount traded
        '''
        blockType, _blockSpecs = blockName
        
        if blockType == 'Calib':
            return self.calibrateSOD( 
                            blockName   = blockName, 
                            params      = params,
                            spparams    = spparams, 
                            calibData   = calibData, 
                            cachedCalib = cachedCalib, 
                            auxParams   = auxParams, 
                            tradeParams = tradeParams )
        
        elif blockType == 'Update':
            return self.calibrateUpdate( 
                            blockName   = blockName, 
                            params      = params, 
                            calibData   = calibData, 
                            cachedCalib = cachedCalib, 
                            auxParams   = auxParams, 
                            tradeParams = tradeParams )

        else:
            raise ValueError( 'Unknown blockType = %s' % str( blockType ) )
        
    def calibrateSOD( self, blockName, params, spparams, calibData, cachedCalib, auxParams, tradeParams ): 

        # compareCached   = params.get( 'CompareCached', False )        
        blockData       = calibData[ blockName  ]

        # ('Calib', ('SOD', '0'))
        _opType, (_opTag, opTagId) = blockName

        dates           = blockData[ 'dates'    ]
        adjclose        = blockData[ 'adjclose' ]
        # adjclose        = blockData[ 'close' ]
        symbols         = blockData[ 'symbols'  ]
        
        shrinkage       = params[ 'Shrinkage' ]
        highLowScale    = params[ 'HighLowScale' ]
        
        count           = 30
        k               = 5
        
        opTagId         = int( opTagId )
        if opTagId == 0:
            cachedCalib[ 'openPrice' ]  = adjclose
        elif opTagId == 1:
            cachedCalib[ 'highPrice' ]  = adjclose
        elif opTagId == 2:
            cachedCalib[ 'lowPrice' ]   = adjclose
        elif opTagId == 3:
            cachedCalib[ 'closePrice' ] = adjclose
            
            x = colcal.adjustHighLow( cachedCalib[ 'openPrice' ], cachedCalib[ 'highPrice' ], cachedCalib[ 'lowPrice' ], cachedCalib[ 'closePrice' ] )
            cachedCalib[ 'HighLowCalib' ] = { 
                'openPrice' : x[0], 
                'highPrice' : x[1], 
                'lowPrice'  : x[2], 
                'closePrice': x[3], 
            }
            lastCalibDate = dates[-1]
            # selector = colcal.fieldSelector( 'absz' )
            selector = colcal.fieldSelector( 'absmean' )
            # selector = colcal.fieldSelector( 'mean' )
            
            cachedCalib[ 'BoundObject' ] = colcal.calibrate( 
                                                symbols=symbols, 
                                                lastCalibDate=lastCalibDate, 
                                                cachedCalib=cachedCalib, 
                                                selector=selector, 
                                                count=count,
                                                highLowScale=highLowScale,
                                                shrinkage=shrinkage,
                                                k=k,
                                                **cachedCalib[ 'HighLowCalib' ] )
        sharesInfo      = { 
            'TradeSymbols'  : symbols,
            'TradeShares'   : None,
        }            
        return cachedCalib, sharesInfo

    def calibrateUpdate( self, blockName, params, calibData, cachedCalib, auxParams, tradeParams ): 
        # ( 'Update',( ( 'LTS', '0' ), ( 'SOD', '0' ) ), 'nxc_lasttrade_352'      ), 
        # compareCached = params.get( 'CompareCached', False )
        
        _blockType,   blockSpecs = blockName
        _updateSpecs, calibSpecs = blockSpecs
        (_opTag, opTagId) = calibSpecs

        opTagId     = int( opTagId )
#        opMode      = twkval.getenv( 'run_mode')
#        oldCalibData= calibData[ ( 'Calib', calibSpecs ) ]
        
#        if opMode in ('sim-prod', 'trade-prod'):
#            symbols = cachedCalib[ 'symbols'    ]
#        else:
#            symbols = oldCalibData[ 'symbols'   ]

        blockData   = calibData[ blockName  ]        
        dates       = blockData[ 'dates'    ]
        # adjclose    = blockData[ 'close'    ]
        symbols     = blockData[ 'symbols'  ]
        adjclose    = blockData[ 'adjclose' ]
        slices      = None
        
        opTagId         = int( opTagId )
        if opTagId == 0:
            cachedCalib[ 'openPrice' ]  = adjclose
        elif opTagId == 1:
            cachedCalib[ 'highPrice' ]  = adjclose
        elif opTagId == 2:
            cachedCalib[ 'lowPrice' ]   = adjclose
        elif opTagId == 3:
            cachedCalib[ 'closePrice' ] = adjclose
            x = colcal.adjustHighLow( cachedCalib[ 'openPrice' ], cachedCalib[ 'highPrice' ], cachedCalib[ 'lowPrice' ], cachedCalib[ 'closePrice' ] )
            cachedCalib[ 'HighLowCalib' ] = { 
                'openPrice' : x[0][-1,:], 
                'highPrice' : x[1][-1,:], 
                'lowPrice'  : x[2][-1,:], 
                'closePrice': x[3][-1,:], 
            }
            tradeDate   = dates[-1]
            params      = { 'HoldingPeriod' : 5 }
            slices      = self.updatePositions( params, symbols=symbols, cachedCalib=cachedCalib, tradeDate=tradeDate )
            
        sharesInfo  = { 
         'SliceTradeShares' : slices,
         'TradeShares'      : None,
         'TradeSymbols'     : symbols,
        }
        
        return cachedCalib, sharesInfo

    def updatePositions( self, params, symbols, cachedCalib, tradeDate ):
        highLow         = cachedCalib[ 'HighLowCalib'   ]        
        boundObj        = cachedCalib[ 'BoundObject'    ]
        boundObjs       = cachedCalib[ 'BoundObjects'   ]
        
        boundObjs.append( boundObj )
        
        return colut.managePos( params=params, symbols=symbols, boundObjs=boundObjs, highLow=highLow )
