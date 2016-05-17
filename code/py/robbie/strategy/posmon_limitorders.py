import os
import numpy
import warnings
import math as math

import robbie.lib.io as io
import robbie.tweak.value as twkval

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
        
        if self._pprices == None:
            # first time
            # there is no pnl
            avgprices   = prices
            unrlzds     = numpy.zeros( len( symbols ) )
            rlzds       = numpy.zeros( len( symbols ) )
        else:            
            unrlzds, rlzds, avgprices = computePnl( shares, prices, self._positions, self._pprices )
        
        self._updatePnl( date, symbols, unrlzds, rlzds )        
        self._pprices    = avgprices
        self._positions += shares
        
        self._updateTrades( date, symbols, shares, prices, avgprices, self._positions )
        self._updateEquityCurve( date, symbols, unrlzds, rlzds, avgprices, self._positions, costs )
    