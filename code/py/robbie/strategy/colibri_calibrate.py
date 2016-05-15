'''
'''

import numpy

from operator import itemgetter

import meadow.lib.fetch as libfetch
from   meadow.lib.logging import logger
import meadow.strategy.colibri_util as cut
import meadow.math.cvxprog.bqpfhdit as bqpfhdit
import meadow.math.factor.expectedmax as expectedmax 
import meadow.math.shrinkage.oracleshrink as oracleshrink

fields  = (  'b_low', 'b_high', 'pnl', 'std', 'mean', 'absz', 'absmean' )
fix     = dict( ( n, i ) for ( i, n ) in enumerate( fields ) )

def fieldSelector( name ):
    def _selector( _results ):
        n = fix[ name ]
        return sorted(_results, key=itemgetter(n))
    return _selector

def meanSelector( _results ):
    n = fix[ 'mean' ]
    return sorted(_results, key=itemgetter(n))

def calc_absz( mean, std ):
    if mean == 0 and std == 0:
        return 0
    return abs( mean/std ) 

def newSessionId():
    return id( [] )

class BoundObj( object ):
    
    def __init__(self, symbols, qtys, bounds ):
        self._bounds    = bounds
        self._six       = dict( ( s,i ) for ( i,s ) in enumerate( symbols ) )
        self._symbols   = symbols
        self._qtys      = qtys
        self._positions = numpy.zeros( len( symbols ) )
        self._currentSessionId = None
        self._session   = {}
        self._openPrice = None

    def openPrice( self ):
        return self._openPrice

    def setOpenPrice( self, o ):
        assert self._openPrice == None
        self._openPrice = o
        
    def startSession( self ):
        sessionId = newSessionId()
        self._currentSessionId = sessionId
        self._session[ sessionId ] = { 
            'high'  : numpy.zeros( len( self._symbols ) ),
            'low'   : numpy.zeros( len( self._symbols ) ),
        }
        return sessionId

    def endSession(self, sessionId ):
        s = self._session[ sessionId ].copy()
        del self._session[ sessionId ]
        self._currentSessionId = None
        return s
        
    def bounds(self):
        return self._bounds

    def isAvailHighByIx(self, ix ):
        ssn = self._session[ self._currentSessionId ]
        return ssn[ 'high' ][ ix ] == 0        

    def isAvailLowByIx(self, ix ):
        ssn = self._session[ self._currentSessionId ]
        return ssn[ 'low' ][ ix ] == 0        
        
    def takeHighByIx(self, ix ):
        ssn = self._session[ self._currentSessionId ]        
        assert ssn[ 'high' ][ ix ] == 0        
                
        qty = self._qtys[ ix ]
        ssn[ 'high' ][ ix ] += -qty
            
        self._positions[ ix ] += ssn[ 'high' ][ ix ]
        return ssn[ 'high' ][ ix ]

    def takeLowByIx(self, ix ):
        ssn = self._session[ self._currentSessionId ]        
        assert ssn[ 'low' ][ ix ] == 0        
        
        qty = self._qtys[ ix ]        
        ssn[ 'low' ][ ix ] += qty

        self._positions[ ix ] += ssn[ 'low' ][ ix ]
        return ssn[ 'low' ][ ix ]

    def takePositions(self):
        p = self._positions.copy()
        self._positions[:] = 0
        return p
    
    def __repr__(self):
        return 'BoundObj( symbols=%s, qtys=%s, bounds=%s )' % ( str( self._symbols ), str( self._qtys ), str( self._bounds ) )

_x = None

def calibrate( symbols, lastCalibDate, cachedCalib, count, highLowScale, shrinkage, k, openPrice, highPrice, lowPrice, closePrice, selector ):
    isDumping = False
    
    results = []
    highPrice, lowPrice, openPrice, closePrice = highPrice.copy(), lowPrice.copy(), openPrice.copy(), closePrice.copy() 
    
    for _six, ( h, l, o, c ) in enumerate( zip( highPrice.T, lowPrice.T, openPrice.T, closePrice.T ) ):    
        N   = cut.py_me0( k=k, highPrice=h, lowPrice=l, openPrice=o, closePrice=c )
        
        h   = numpy.array( h[:N], float )
        l   = numpy.array( l[:N], float )
        o   = numpy.array( o[:N], float )
        c   = numpy.array( c[:N], float )

        ol  = numpy.max( o - l ) * highLowScale
        ho  = numpy.max( h - o ) * highLowScale
        upper, lower = ho, ol

        pnl     = numpy.zeros( N )
        state   = numpy.zeros( N )
        
        _results = []
        for b_low in numpy.arange( 0, lower, lower/count ):
            b_low = float( b_low )
            for b_high in numpy.arange( 0, upper, upper/count ):
                b_high = float( b_high )
                cut.s0( highPrice=h, lowPrice=l, openPrice=o, closePrice=c, b_low=b_low, b_high=b_high, pnl=pnl, state=state )
                std     = pnl.std()
                mean    = pnl.mean()                
                absz    = calc_absz( mean=mean, std=std )
                absmean = abs( mean )
                _results.append( (  b_low, b_high, pnl.copy(), std, mean, absz, absmean ) )
                # print '%3d %5.2f %5.2f %5.2f %5.2f %5.2f' % ( _six, b_low, b_high, absz, mean, std )

        if isDumping:    
            fetchName = ( 
                ( 'type', 'results' ),
                ( 'lastCalibDate', lastCalibDate ), 
                ( 'six', _six ), 
            )
            libfetch.dump( name=fetchName, obj=_results, debug=True )
                
        r = selector( _results )[-1]
        results.append( r )

    r0  = results.pop(0)
    pnl = r0[ fix['pnl'] ]
    mat = numpy.reshape( pnl, ( 1, -1 ) )
    bounds  = [ ( r0[ fix[ 'b_low' ]], r0[ fix[ 'b_high' ]] ) ]        
    for r0 in results:
        pnl = r0[ fix['pnl'] ]
        pnl = numpy.reshape( pnl, ( 1, -1 ) )
        mat = numpy.vstack( [ mat, pnl ] )
        b   = ( r0[ fix[ 'b_low' ] ], r0[ fix[ 'b_high' ] ] )
        bounds.append( b )        
    
    mat = mat.T

    if isDumping:    
        fetchName = ( 
            ( 'type', 'mat' ),
            ( 'lastCalibDate', lastCalibDate ), 
        )
        libfetch.dump( name=fetchName, obj=mat, debug=True )
        fetchName = ( 
            ( 'type', 'bounds' ),
            ( 'lastCalibDate', lastCalibDate ), 
        )
        libfetch.dump( name=fetchName, obj=bounds, debug=True )

        obj = ( highPrice, lowPrice, openPrice, closePrice )
        fetchName = ( 
            ( 'type', 'prices' ),
            ( 'lastCalibDate', lastCalibDate ), 
        )
        libfetch.dump( name=fetchName, obj=obj, debug=True )


        import sys
        sys.exit()
        
    # initweight = cachedCalib[ 'CurrPort' ]
    initweight = numpy.zeros( cachedCalib[ 'CurrPort' ].shape )
    # C   = numpy.cov( mat.T )
    C,_ = oracleshrink.oracleShrink( mat.T )
    f0  = numpy.mean( mat, 0 )
    risklambda = .001

    lb0 = numpy.ones( C.shape[0] ) * -1000000 * 100
    ub0 = numpy.ones( C.shape[0] ) *  1000000 * 100
    
    # initweight, f0, lb0, ub0
    # x   = _optimze( initweight=initweight, C=C, f0=f0, risklambda=risklambda, lb0=lb0, ub0=ub0, sk=shrinkage )
    
    x = numpy.sign( f0 )
    logger.debug('calibrate x=%s' % str( x ) )
    return BoundObj( symbols=symbols, qtys=x, bounds=bounds )

def adjustHighLow( openPrice, highPrice, lowPrice, closePrice ):
    
    lowPrice[ lowPrice > openPrice ]    = openPrice[ lowPrice > openPrice ]
    lowPrice[ lowPrice > closePrice ]   = closePrice[ lowPrice > closePrice ]
    highPrice[ highPrice < openPrice ]  = openPrice[ highPrice < openPrice ]
    highPrice[ highPrice < closePrice ] = closePrice[ highPrice < closePrice ]
    
    return openPrice, highPrice, lowPrice, closePrice

def _optimze( initweight, C, f0, risklambda, lb0, ub0, sk = 0.1 ):
    # initweight - in dollar
    # sk -> 0..1; the higher the number the less information is retained.
    
    nit     = 1000
    # increase cost for select tickers
    rmw     = numpy.zeros( ( len( initweight ), 1 ) )
    qcost   = 0
    lcost   = .01
    
    # Tengjie suggest for the N=10, to choose d=3
    d       = int( C.shape[0] / 3 )
    D,V = expectedmax.guesser( C, d )
    
    # D -> N,N, V -> N,d
    # D,V = expectedmax.factorEM( D, V, C, nit, sk )
    try:
        D,V = expectedmax.factorEM( D, V, C, nit, sk )
    except:
        raise
         
    # f0 - is the return 
    # risklambda -> 
    x, _error, count = bqpfhdit.bqpfhditSD_rmw( 
            initweight=initweight, 
            D1=D, V1=V, 
            risklambda=risklambda, 
            f0=f0, 
            lcost=lcost, 
            qcost=qcost, 
            lb0=lb0, ub0=ub0, s=True, rmw=rmw )
    
    # logger.debug('_optimze: nit=%d count=%d' % ( nit, count ) )
    return [ int(e) for e in x.ravel() ]
