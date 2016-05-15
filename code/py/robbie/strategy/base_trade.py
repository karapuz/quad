'''
    strategies

'''

import numpy
from   meadow.lib.logging import logger
import meadow.tweak.value as twkval

def roundShares( tradeShares ):
    return numpy.round( tradeShares )

def ptl (shares , tradeBlockId, splitRuleArgs):
    zerotrades   = len(numpy.where(shares==0)[0])
    nzerotrades  = len(shares) - zerotrades
    shareix      = numpy.absolute(shares).argsort()
    if splitRuleArgs==3:
        if tradeBlockId==0:
            shares[ shareix[ zerotrades : zerotrades + int( 0.7 * nzerotrades) ] ] = 0
        elif tradeBlockId==1:
            shares[ shareix[ zerotrades : zerotrades + int( 0.4 * nzerotrades) ] ] = 0  
        return shares
    elif splitRuleArgs==5:
        if tradeBlockId==0:
            shares[ shareix[ zerotrades : zerotrades + int( 0.8 * nzerotrades) ] ] = 0
        elif tradeBlockId==1:
            shares[ shareix[ zerotrades : zerotrades + int( 0.6 * nzerotrades) ] ] = 0  
        elif tradeBlockId==2:
            shares[ shareix[ zerotrades : zerotrades + int( 0.4 * nzerotrades) ] ] = 0 
        elif tradeBlockId==3:
            shares[ shareix[ zerotrades : zerotrades + int( 0.2 * nzerotrades) ] ] = 0 
        return shares

def _splitShares(tradeParams , blockName, shares, multiPeriodTrades):
    
    tradeBlockName, dataBlockName = blockName
    tradeBlockType, tradeBlockId = dataBlockName[0]
    
    splitRule       = tradeParams[ 'TradeSplitRule'     ]
    
    if splitRule == 'Uniform_Update':
        splitRuleArgs   = tradeParams[ 'TradeSplitRuleArgs' ]
        shares /= ( float( splitRuleArgs ) - int(tradeBlockId) )  
    elif splitRule == 'Once':
        shares = shares
    elif splitRule == 'Uniform_Noupdate':
        splitRuleArgs   = tradeParams[ 'TradeSplitRuleArgs' ]
        #shares /= ( float( splitRuleArgs ) )     
        if not multiPeriodTrades:
            leftShares = shares
        else:
            for trades in multiPeriodTrades: 
                shares -= trades['TradeShares']
            leftShares = shares
        shares      = leftShares / ( float( splitRuleArgs ) - int(tradeBlockId) )
    elif splitRule == 'Uniform_Noupdate_ptl':
        shares          = ptl( shares, tradeBlockId )
        splitRuleArgs   = tradeParams[ 'TradeSplitRuleArgs' ]   
        if not multiPeriodTrades:
            leftShares = shares
        else:
            for trades in multiPeriodTrades: 
                shares -= trades['TradeShares']
            leftShares = shares
        shares      = leftShares / ( float( splitRuleArgs ) - int(tradeBlockId) )        
    else:
        raise ValueError( 'Unknown TradeSplitRule = %s' % str( splitRule ) )
    return shares

def splitShares(tradeParams , blockName, shares, cachedCalib):
    
    _tradeBlockName, dataBlockName = blockName
    _tradeBlockType, tradeBlockId = dataBlockName[0]
    
    splitRule       = tradeParams[ 'TradeSplitRule'     ]
    splitRuleArgs   = tradeParams[ 'TradeSplitRuleArgs' ]
    
    if splitRule == 'Uniform_Update':
        #splitRuleArgs   = tradeParams[ 'TradeSplitRuleArgs' ]
        shares /= ( float( splitRuleArgs ) - int(tradeBlockId) )  
    elif splitRule == 'Once':
        shares = shares   
    elif splitRule == 'Uniform_Noupdate_ptl':
        shares          = ptl( shares, int(tradeBlockId), splitRuleArgs)
        leftShares      = shares - ( cachedCalib['CurrPort'] - cachedCalib['SODPort'] )
        shares          = leftShares / ( float( splitRuleArgs ) - int(tradeBlockId) )
    elif splitRule == '100shares_per_second':
        shares = shares.flatten() - ( cachedCalib['CurrPort'].flatten() - cachedCalib['SODPort'].flatten() )
        not_trade = [shares <= (tradeParams[ 'TradeTimes' ] - int(tradeBlockId) - 1) * 200 * 60 ]
        shares[not_trade] = 0
        to_trade =numpy.logical_not(numpy.array(not_trade).flatten()) 
        shares[to_trade] = shares[to_trade] -  (tradeParams[ 'TradeTimes' ] - int(tradeBlockId) - 1) * 200 * 60 
        if int(tradeBlockId)==0:
            print 'big trade : ',sum(to_trade)
    else:
        raise ValueError( 'Unknown TradeSplitRule = %s' % str( splitRule ) )
    return shares

def sa_trade( params, tradeData, calibData, sharesInfo ):
    tradedPos = {
        'TradeShares'       : sharesInfo[ 'TradeShares'   ],
        'TradeSymbols'      : sharesInfo[ 'TradeSymbols'  ],
        'TradePrices'       : tradeData[ 'adjclose'       ],
    }
    return tradedPos

def sa_tradeWithTransactionCostsByBasisPoints( tradeDate, params, tradeData, calibData, sharesInfo ):
    '''
    TCC - transaction costs coefficient
    '''
    shares      = sharesInfo[ 'TradeShares'    ]
    # adjclose    = tradeData[ 'adjclose'        ]

    dates       = tradeData[ 'dates'    ]
    tradeIx     = int( numpy.where( dates == tradeDate )[0] )
    if 'TradePrice' in sharesInfo:
        adjclose = sharesInfo[ 'TradePrice' ]
    else:
        adjclose = tradeData[ 'adjclose' ][ tradeIx, : ]

    costsCoeff  = params[ 'BasisPointsTCC' ] 
    costs       = numpy.abs( shares ) * adjclose * costsCoeff
     
    tradedPos = {
        'TradeShares'   : sharesInfo[ 'TradeShares'   ],
        'TradeSymbols'  : sharesInfo[ 'TradeSymbols'  ],
        'TradePrices'   : adjclose, 
        'TransactionCosts'   : costs, 
    }
    return tradedPos

def sa_tradeWithTransactionCostsByBasisPointsMultiBlock( tradeDate, tradeParams, blockName, specProcData, calibData, sharesInfo, multiPeriodTrades ):
    '''
    TCC - transaction costs coefficient
    '''
    tradeBlockName, dataBlockName = blockName
    tradeBlockType, tradeBlockId = dataBlockName[0]
     
    costsCoeff  = tradeParams[ 'BasisPointsTCC' ]
    price       = calibData[ ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ) ) ]['adjclose'][-1,:] # accounting using 3:51
    price[~numpy.isfinite(price)] = 0  # xu dong modified it:  because it would result in nan costs in posmon. 
    
    #price       = calibData[ ( 'Update', ( ( 'LTS', '2' ), ( 'SOD', '0' ) ) ) ]['adjclose'][-1,:] # accounting using 3:57
    
    priceSymbols= calibData[ ( 'Update', ( ( 'LTS', '0' ), ( 'SOD', '0' ) ) ) ][ 'UpdateSymbols'  ]
    tradeData   = specProcData[ blockName       ]
    dates       = tradeData[ 'dates'    ]
    tradeSymbols= tradeData[ 'symbols'  ]
    tradeIx     = int( numpy.where( dates == tradeDate )[0] )

    if 'TradePrice' in sharesInfo:
        adjclose = sharesInfo[ 'TradePrice' ]
    else:
        adjclose = tradeData[ 'adjclose' ][ tradeIx, : ]

    shares      = sharesInfo [ 'TradeShares'    ]
    shareSymbols= sharesInfo [ 'TradeSymbols'   ]

    sharesix    = ( shares!=0 )
    d0  = dict( (n,i) for (i,n) in enumerate( tradeSymbols ) )
    d1  = dict( (n,i) for (i,n) in enumerate( priceSymbols ) )
    
    preprice    = numpy.zeros( len( shares ) )
    actprice    = numpy.zeros( len( shares ) )    
    actshares   = numpy.zeros( len( shares ) )
    noPrice     = []
    for i,n in enumerate( shareSymbols ):
        if n in d0:
            p     = adjclose[ d0[ n ] ]
            prep  = price   [ d1[ n ] ]
            if p:
                preprice[ i ] = prep
                actprice[ i ] = p
                actshares[ i ] = shares[ i ]
            else:
                if shares[ i ] == 0:
                    actshares[ i ] = 0                    
                    actprice[ i ]  = prep
                    preprice[ i ]  = prep
                else:
                    actshares[ i ] = shares[ i ]
                    actprice[ i ]  = prep  # modified by xu dong
                    preprice[ i ]  = prep  # modified by xu dong
                    noPrice.append( i )
                
    costs = numpy.abs( actshares ) * actprice * costsCoeff
    shiftedCosts = (actprice-preprice)*actshares # Tengjie needs this for his accounting
    
    marketSlippage = twkval.getenv( 'sim_marketSlippage' )
    if marketSlippage != None:
        logger.debug( 'marketSlippage: %s' % str( marketSlippage ) )        
        ( slipageType, slippageData ) = marketSlippage
        slippageData = float( slippageData )
        
        instrN = len( actshares )
        # Kill Uniform Shares
        if slipageType == 'xus':
            actshares *= slippageData
        # Kill Uniform Instruments
        elif slipageType == 'xui':
            liveIndex = range( 0, instrN )
            numpy.random.shuffle(liveIndex)
            actshares[ liveIndex[ : int( (1.-slippageData) * instrN ) ] ] = 0
        else:
            raise ValueError( 'Unknown marketSlippage=%s' % str( marketSlippage ) )
    
    if noPrice:
        actualmissed = len( numpy.where(actshares[ sharesix.flatten() ] == 0 )[0] )  #modified by xu dong
        logger.error( 'trade: %d missed instruments total = %4d, actual = %4d' % ( tradeDate, len( noPrice ), actualmissed ) )
        
    tradedPos = {
        'TradeShares'       : actshares,
        'TradeSymbols'      : sharesInfo[ 'TradeSymbols'  ],
        'TradePrices'       : actprice, 
        'TransactionCosts'  : costs, 
        'LastPrices'        : price,
        'shiftedAccCosts'   : shiftedCosts, 
    }
    return tradedPos
