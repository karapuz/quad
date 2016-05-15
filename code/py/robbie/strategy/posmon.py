import os
import numpy
import warnings
import math as math

import meadow.lib.io as io
import meadow.tweak.value as twkval

class StoredPositionData():
    def __init__(self):
        self.positionData = []
        self.computedMetrics = []
        self.symbList = []
    def setSymbolList( self, symbList ):
        self.symbList = symbList
    def addDayPositions( self, date, shares, dollarPos ):
        self.positionData.append ( ( date, shares, dollarPos ) )
    def addDayComputedMetrics( self, date, gross, costs ):
        self.computedMetrics.append ( ( date, gross, costs ) )

def computePnl( shares, prices, positions, pprices ):
    rlzds       = numpy.zeros( len( shares ) )
    unrlzds     = numpy.zeros( len( shares ) )
    avgprices   = numpy.zeros( len( shares ) )
    
    ix  = 0
    for share, price, pos, pprice in zip(shares, prices, positions, pprices ):
        if share * pos >= 0:
            # same direction. no realized pnl
            if share + pos:
                ap  = ( share * price + pos * pprice ) / float( share + pos )
            else:
                ap  = price
            rlzd    = 0
            
        elif share * pos < 0:
            # same direction. no realized pnl
            if abs( pos ) >= abs( share ):
                ap  = pprice
                rlzd= share * ( pprice - price )
            else:
                ap  = price
                rlzd= pos * ( price - pprice )
                
        avgprices   [ ix ]  = ap
        unrlzds     [ ix ]  = ( pos + share ) * ( ap - price )
        rlzds       [ ix ]  = rlzd        
        ix += 1

    return unrlzds, rlzds, avgprices

def computePnlMrk2Mkt( shares, prices, positions, pprices ):
    rlzds       = numpy.zeros( len( shares ) )
    unrlzds     = numpy.zeros( len( shares ) )
    currPrices  = numpy.zeros( len( shares ) )
    
    ix  = 0
    for share, price, pos, pprice in zip(shares, prices, positions, pprices ):
        currPrices  [ ix ]  = price
        unrlzds     [ ix ]  = ( pos  ) * ( price - pprice )
        ix += 1

    return unrlzds, rlzds, currPrices

def computePnlMrk2MktAvg( shares, prices, positions, pprices ):
    rlzds       = numpy.zeros( len( shares ) )
    unrlzds     = numpy.zeros( len( shares ) )
    currPrices  = numpy.zeros( len( shares ) )
    ix  = 0
    for share, price, pos, pprice in zip(shares, prices, positions, pprices ):
        currPrices  [ ix ]  = price
        dp = price - pprice
        if not numpy.isfinite( dp ):
            dp = 0
        unrlzds     [ ix ]  = ( pos  ) * ( dp )
        ix += 1

    return unrlzds, rlzds, currPrices

def computePnlMrk2MktNaN( shares, prices, positions, pprices ):
    rlzds       = numpy.zeros( len( shares ) )
    unrlzds     = numpy.zeros( len( shares ) )
    currPrices  = numpy.zeros( len( shares ) )
    ix  = 0
    dround = lambda x,d: round(x,d - int(math.ceil(math.log10(abs(x))))) if x>0 else x
    for share, price, pos, pprice in zip(shares, prices, positions, pprices ):
        currPrices  [ ix ]  = price
        dp = dround(price, 12) - dround(pprice, 12)
        # the above is modified by xu dong, need an indicator in parameters to indcate if to round or not.
        if (not numpy.isfinite( dp )) or (price==0):
            dp = 0
            currPrices[ ix ] = pprice
        unrlzds[ ix ]  = ( pos  ) * ( dp )
        ix += 1
    print sum(unrlzds), sum(positions)
    return unrlzds, rlzds, currPrices


class PositionMonitor( object ):
    
    def __init__(self, dirName, symbols, recordPositionHistory=False, positions=None ):
        self._eqch      = [ 
            'Costs', 'Unrealized', 'Realized', 
            'Daily Gross', 
            'Daily Net', 
            'Gross Cum.', 
            'Net Cum.',
            'Net/Gross Ratio',
            'Sharpe', 
            '#Pos', '#Neg',
            'Port. Cap', 'Port. Full', 'Port. Full/Cap'
        ]
        self._initEqCurveIxs()
        
        self._dirName   = dirName
        self._symbols   = symbols
        self._pprices   = None
        
        self.storeHistory = recordPositionHistory
        
        self._init( symbols=symbols, positions=positions )

    def doMrk2Mkt(self, date, marketPrice, marketSymbols, costs ):
        mrktS2P  = dict( ( s,p ) for s,p in zip ( marketSymbols, marketPrice ) )        
        vals    = []
        cost    = sum( costs )
        for avgSym, avgPrice, avgPos in zip ( self._symbols, self._pprices, self._positions  ):            
            vals.append( ( mrktS2P[ avgSym ] - avgPrice ) * avgPos )        
        vals.append( cost )
        
        s = io.arr2csv( [str(date)] + io.arr2list( vals ) ) + '\n'
        self._mrk2mkt.write( s )
        
    def doMrk2Mkt_TJ(self, date, eodPrice, eodpPrice, marketSymbols, costs, shares ):
        eodS2P  = dict( ( s,p ) for s,p in zip ( marketSymbols, eodPrice ) )
        eodpS2P  = dict( ( s,p ) for s,p in zip ( marketSymbols, eodpPrice ) )        
        vals    = []
        valsm   = []
        pos     = []
        prdf    = []
        for avgSym, avgPrice, avgPos, share in zip ( self._symbols, self._pprices, self._positions, shares  ):            
            vals.append( ( eodS2P[ avgSym ] - eodpS2P[ avgSym ] ) * ( avgPos - share ) )
            valsm.append( (eodS2P[ avgSym ] - avgPrice ) * share )
            pos.append( avgPos - share )
            prdf.append( eodS2P[ avgSym ] - eodpS2P[ avgSym ] )        
        p  = io.arr2csv( [str(date)] + io.arr2list( pos ) ) + '\n' + io.arr2csv( [str(date)] + io.arr2list( prdf ) ) + '\n'
        s0 = io.arr2csv( [str(date)] + io.arr2list( vals ) ) + '\n' + io.arr2csv( [str(date)] + io.arr2list( valsm ) ) + '\n'
        v_all = numpy.array([sum(vals), sum(valsm), sum(costs)]) 
        s1 = io.arr2csv( [str(date)] + io.arr2list( v_all ) ) + '\n'
        s  = p + s0 + s1 
        self._mrk2mkt_TJ.write( s )
        
     
    def _init(self, symbols, positions ):        
        self._symbols   = symbols
        self._positions = numpy.array( positions ) if len( positions ) else numpy.zeros( len( symbols ) )
        
        self._tfd       = self._initiateWithHeader( 'shares.csv' )
        self._pricefd   = self._initiateWithHeader( 'prices.csv' )
        self._rlzdfd    = self._initiateWithHeader( 'realized.csv' )
        self._unrlzdfd  = self._initiateWithHeader( 'unrealized.csv' )
        self._fullfd    = self._initiateWithHeader( 'full.csv', symbols.tolist() + ['Full'] )
        self._eqcfd     = self._initiateWithHeader( 'equitycurve.csv', self._eqch )

        self._avgpricefd= self._initiateWithHeader( 'avgprice.csv' )
        self._portfd    = self._initiateWithHeader( 'portfolio.csv' )
        self._mrk2mkt   = self._initiateWithHeader( 'mrk2mrkt.csv', symbols.tolist() + ['Costs'] )
        self._mrk2mkt_TJ   = self._initiateWithHeader( 'mrk2mrkt_TJ.csv', symbols.tolist() )
        
        if self.storeHistory:
            self.storedPositions = StoredPositionData()
            self.storedPositions.setSymbolList( symbols )

    def _initEqCurveIxs(self):
        self._eqchix = dict( (n,i) for (i,n) in enumerate( self._eqch ) )
        a = []
        self._eqcvals = [ a[:] for _ in xrange( len( self._eqch ) ) ]

    def _initiateWithHeader(self, fn, header=None ):
                    
        if not header:
            header = self._symbols
            
        fd = open( os.path.join( self._dirName, fn ), 'w' )
        fd.write( io.arr2csv( [''] + io.arr2list( header ) ) + '\n' )
        return fd
    
    def _validate(self, symbols ):
        assert( numpy.all( self._symbols == symbols ) )

    def _updateTrades( self, date, symbols, shares, prices, avgprices, positions ):
        s = io.arr2csv( [str(date)] + io.arr2list( shares ) ) + '\n'
        self._tfd.write( s )
        self._tfd.flush()

        s = io.arr2csv( [str(date)] + io.arr2list( prices ) ) + '\n'
        self._pricefd.write( s )
        self._pricefd.flush()

        s = io.arr2csv( [str(date)] + io.arr2list( avgprices ) ) + '\n'
        self._avgpricefd.write( s )
        self._avgpricefd.flush()

        s = io.arr2csv( [str(date)] + io.arr2list( positions ) ) + '\n'
        self._portfd.write( s )
        self._portfd.flush()
        
    def _updatePnl( self, date, symbols, unrlzds, rlzds ):
        s = io.arr2csv( [str(date)] + io.arr2list( rlzds ) ) + '\n'
        self._rlzdfd.write( s )
        
        s = io.arr2csv( [str(date)] + io.arr2list( unrlzds ) ) + '\n'
        self._unrlzdfd.write( s )
        
        eqc = rlzds + unrlzds
        s   = io.arr2csv( [str(date)] + io.arr2list( eqc ) + [ sum ( eqc ) ] ) + '\n'
        self._fullfd.write( s )

    def _updateEquityCurve( self, date, symbols, unrlzds, rlzds, avgprices, positions, costs ):
        '''[ 'Unrealized', 'Realized', 'Full Position', 'Cumulative', 'Sharpe', '#Pos', '#Neg' ]
        '''
        costsix     = self._eqchix[ 'Costs'         ]
        unrlzdix    = self._eqchix[ 'Unrealized'    ]
        rlzdix      = self._eqchix[ 'Realized'      ]
        dailygrossix= self._eqchix[ 'Daily Gross'   ]
        dailynetix  = self._eqchix[ 'Daily Net'     ]
        grosscumix  = self._eqchix[ 'Gross Cum.'    ]
        netcumix    = self._eqchix[ 'Net Cum.'      ]
        ngrix       = self._eqchix[ 'Net/Gross Ratio' ]

        shix        = self._eqchix[ 'Sharpe'        ]
        posix       = self._eqchix[ '#Pos'          ]
        negix       = self._eqchix[ '#Neg'          ]

        portcapix   = self._eqchix[ 'Port. Cap'     ]
        portfullix  = self._eqchix[ 'Port. Full'    ]
        portpfratix = self._eqchix[ 'Port. Full/Cap']

        vals        = numpy.zeros( len( self._eqch ) )
        
        _dailyCosts = numpy.sum( costs )
        self._eqcvals[ costsix ].append( _dailyCosts )

        if twkval.getenv( 'report_shiftedCosts' ):
            if len( self._eqcvals[ costsix ] ) > 1:
                dailyCosts = self._eqcvals[ costsix ][-2]
            else:
                dailyCosts = 0
        else:
            dailyCosts = self._eqcvals[ costsix ][-1]
                        
        vals[ costsix   ]   = dailyCosts
        vals[ unrlzdix  ]   = numpy.sum( unrlzds    )
        vals[ rlzdix    ]   = numpy.sum( rlzds      )
        
        self._eqcvals[ rlzdix   ].append( vals[ rlzdix ] )
        
        cumPnl  = vals[ unrlzdix  ] + sum( self._eqcvals[ rlzdix ] )
        lcumPnl = self._eqcvals[ grosscumix ] if self._eqcvals[ grosscumix ] else 0
        
        daily   = cumPnl - lcumPnl
        
        vals[ grosscumix    ]  = cumPnl
        vals[ netcumix      ]  = vals[ grosscumix] - numpy.sum( self._eqcvals[ costsix ] )
        vals[ dailygrossix  ]  = daily
        vals[ dailynetix    ]  = daily - dailyCosts
        
        if vals[ grosscumix ] > 0 and vals[ netcumix ] > 0:
            vals[ ngrix     ]  = vals[ netcumix ] / vals[ grosscumix ]
        else:
            vals[ ngrix     ]  = 0
        
       # vals[ ngrix         ]  = 1 - dailyCosts / numpy.abs( daily ) if daily else 0
        
        self._eqcvals[ netcumix     ].append( vals[ netcumix   ] )
        self._eqcvals[ grosscumix   ] = cumPnl
        self._eqcvals[ dailygrossix ].append( daily )
        self._eqcvals[ dailynetix   ].append( vals[ dailynetix ] )

        pnls    = numpy.array( self._eqcvals[ dailynetix ] )
        
        mean_   = numpy.mean( pnls )
        std_    = numpy.std( pnls )

        if std_:
            sharpe = mean_/std_ * numpy.sqrt( 252 )
        else:
            sharpe = 0
            
        vals[ shix  ]   = sharpe
        vals[ posix ]   = numpy.sum( pnls >= 0 )
        vals[ negix ]   = len( pnls ) - vals[ posix  ]        

        portcapix   = self._eqchix[ 'Port. Cap'     ]
        portfullix  = self._eqchix[ 'Port. Full'    ]
        portpfratix = self._eqchix[ 'Port. Full/Cap']
        
        portfull    = numpy.sum( avgprices * positions ) 
        portcap     = numpy.sum( numpy.abs ( avgprices * positions ) )
        
        vals[ portcapix ]   = portcap
        vals[ portfullix ]  = portfull
        vals[ portpfratix ] = portfull/portcap

        s = io.arr2csv( [str(date)] + io.arr2list( vals ) ) + '\n'
        self._eqcfd.write( s )
        
    def _updateEquityCurveMrk2Mkt( self, date, symbols, unrlzds, rlzds, avgprices, positions, costs ):
        '''[ 'Unrealized', 'Realized', 'Full Position', 'Cumulative', 'Sharpe', '#Pos', '#Neg' ]
        '''
        costsix     = self._eqchix[ 'Costs'         ]
        unrlzdix    = self._eqchix[ 'Unrealized'    ]
        rlzdix      = self._eqchix[ 'Realized'      ]
        dailygrossix= self._eqchix[ 'Daily Gross'   ]
        dailynetix  = self._eqchix[ 'Daily Net'     ]
        grosscumix  = self._eqchix[ 'Gross Cum.'    ]
        netcumix    = self._eqchix[ 'Net Cum.'      ]
        ngrix       = self._eqchix[ 'Net/Gross Ratio' ]

        shix        = self._eqchix[ 'Sharpe'        ]
        posix       = self._eqchix[ '#Pos'          ]
        negix       = self._eqchix[ '#Neg'          ]

        portcapix   = self._eqchix[ 'Port. Cap'     ]
        portfullix  = self._eqchix[ 'Port. Full'    ]
        portpfratix = self._eqchix[ 'Port. Full/Cap']

        vals        = numpy.zeros( len( self._eqch ) )
        
        _dailyCosts = numpy.sum( costs )
        self._eqcvals[ costsix ].append( _dailyCosts )

        if twkval.getenv( 'report_shiftedCosts' ):
            if len( self._eqcvals[ costsix ] ) > 1:
                dailyCosts = self._eqcvals[ costsix ][-2]
            else:
                dailyCosts = 0
        else:
            dailyCosts = self._eqcvals[ costsix ][-1]
                        
        vals[ costsix   ]   = dailyCosts
        vals[ unrlzdix  ]   = numpy.sum( unrlzds    )
        vals[ rlzdix    ]   = numpy.sum( rlzds      )
        
        self._eqcvals[ rlzdix   ].append( vals[ rlzdix ] )
        
        daily  = vals[ unrlzdix  ] + sum( self._eqcvals[ rlzdix ] )
        #lcumPnl = self._eqcvals[ grosscumix ] if self._eqcvals[ grosscumix ] else 0
        
        vals[ grosscumix    ]  = daily + sum(self._eqcvals[ dailygrossix ])
        vals[ netcumix      ]  = vals[ grosscumix] - numpy.sum( self._eqcvals[ costsix ][:-1] )
        vals[ dailygrossix  ]  = daily
        vals[ dailynetix    ]  = daily - dailyCosts
        
        if vals[ grosscumix ] > 0 and vals[ netcumix ] > 0:
            vals[ ngrix     ]  = vals[ netcumix ] / vals[ grosscumix ]
        else:
            vals[ ngrix     ]  = 0
        
       # vals[ ngrix         ]  = 1 - dailyCosts / numpy.abs( daily ) if daily else 0
        
        self._eqcvals[ netcumix     ].append( vals[ netcumix   ] )
        #self._eqcvals[ grosscumix   ]=daily
        self._eqcvals[ dailygrossix ].append( daily )
        self._eqcvals[ dailynetix   ].append( vals[ dailynetix ] )

        pnls    = numpy.array( self._eqcvals[ dailynetix ][1:] )
        
        mean_   = numpy.mean( pnls )
        std_    = numpy.std( pnls )

        if not numpy.isnan( std_ ):
            sharpe = mean_/std_ * numpy.sqrt( 252 )
        else:
            sharpe = 0
            
        vals[ shix  ]   = sharpe
        vals[ posix ]   = numpy.sum( pnls >= 0 )
        vals[ negix ]   = len( pnls ) - vals[ posix  ]        

        portcapix   = self._eqchix[ 'Port. Cap'     ]
        portfullix  = self._eqchix[ 'Port. Full'    ]
        portpfratix = self._eqchix[ 'Port. Full/Cap']
        
        portfull    = numpy.sum( avgprices * positions ) 
        portcap     = numpy.sum( numpy.abs ( avgprices * positions ) )
        
        vals[ portcapix ]   = portcap
        vals[ portfullix ]  = portfull
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vals[ portpfratix ] = portfull/portcap

        s = io.arr2csv( [str(date)] + io.arr2list( vals ) ) + '\n'
        self._eqcfd.write( s )
        self._eqcfd.flush()
                
    def addShares( self, date, symbols, shares, prices, costs ):
        '''
        date       - core
        symbols    - either list, or 1d numpy array
        shares     - either list, or 1d numpy array
        prices     - either list, or 1d numpy array
        costs      - either list, or 1d numpy array
        '''
        # delayed initialization
        if isinstance( symbols, ( tuple, list ) ):
            symbols = numpy.array( symbols )
            
        if self._symbols == None:
            self._init( symbols )

        self._validate( symbols )
        
        mrk2mrkt = twkval.getenv( 'report_useMrk2Mrkt' )
        
        if self._pprices == None:
            # first time
            # there is no pnl
            avgprices   = prices
            unrlzds     = numpy.zeros( len( symbols ) )
            rlzds       = numpy.zeros( len( symbols ) )
        else:
            
            if mrk2mrkt == 'standard':
                unrlzds, rlzds, avgprices = computePnlMrk2Mkt( shares, prices, self._positions, self._pprices )
            elif mrk2mrkt == 'average':
                unrlzds, rlzds, avgprices = computePnlMrk2MktAvg( shares, prices, self._positions, self._pprices )
            elif mrk2mrkt == 'NaN_case':
                unrlzds, rlzds, avgprices = computePnlMrk2MktNaN( shares, prices, self._positions, self._pprices )
            else:
                unrlzds, rlzds, avgprices = computePnl( shares, prices, self._positions, self._pprices )
        
        self._updatePnl( date, symbols, unrlzds, rlzds )        
        self._pprices    = avgprices
        self._positions += shares
        
        if self.storeHistory:
            self.storedPositions.setSymbolList( symbols )
            self.storedPositions.addDayPositions(date, self._positions, self._positions * avgprices)
            totGros = numpy.sum(unrlzds)
            totCosts = numpy.sum(costs)
            self.storedPositions.addDayComputedMetrics(date, totGros, totCosts)

        self._updateTrades( date, symbols, shares, prices, avgprices, self._positions )
        if twkval.getenv( 'report_useMrk2Mrkt') or twkval.getenv( 'report_useMrk2MrktAvg'):
            self._updateEquityCurveMrk2Mkt( date, symbols, unrlzds, rlzds, avgprices, self._positions, costs )
        else:
            self._updateEquityCurve( date, symbols, unrlzds, rlzds, avgprices, self._positions, costs )
    
    def storePosData( self, pklfname ):
        import cPickle as pickle
        with open(pklfname, 'wb') as f:
            pickle.dump(self.storedPositions, f, pickle.HIGHEST_PROTOCOL)

    def removeDelistedSymbols( self, tradeDate ):
        from   meadow.lib.symbChangeDB import symbDB
        
        MIDlist         = self._symbols
        mask            = symbDB.flagListed( MIDlist, date=tradeDate )
        mask_arr        = numpy.array( mask )
        self._symbols   = self._symbols[ mask_arr ]
        self._positions = self._positions[ mask_arr ]
        if self._pprices!=None:
            self._pprices   = self._pprices[ mask_arr ]
        