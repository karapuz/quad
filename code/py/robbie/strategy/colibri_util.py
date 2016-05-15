import numpy
import copy
import meadow.lib.compat as compat
from   meadow.lib.logging import logger
import meadow.tweak.value as twkval
import meadow.rsrch.ivp.driver_util as drut

def c_s0( highPrice, lowPrice, openPrice, closePrice, b_low, b_high, pnl, state ):
    '''
    '''
    from scipy.weave import inline_tools
    n = len( highPrice )
    
    for x in ( lowPrice, openPrice, closePrice ):
        assert( n == len( x ))
    
    code='''
      int i=0;
      int ba = 0;
      int sa = 0;
      float r;
      
      for ( i=0; i<n; i++ ) {
        ba = 0;
        sa = 0;
        r = 0;
        if ( ( openPrice[i] - lowPrice[i] ) >= b_low ) {
            ba = 1;
        };

        
        if ( ( highPrice[i] - openPrice[i] ) >= b_high ) {
            sa = 1;
        };
        
        if ( ba && sa ) {
            pnl[i] = b_low + b_high;;
            state[i] = ba + 10 * sa;
            continue;
        };
        
        if ( ba ) {
            r = closePrice[i] - ( openPrice[i] - b_low );
        };

        if ( sa ) {
            r = ( openPrice[i] + b_high ) - closePrice[i];
        };
        
        pnl[i] = r;
        state[i] = ba + 10 * sa;
        
      };
      return_val=i;
      '''        
    inline_tools.inline( code,
        ['n', 'highPrice', 'lowPrice', 'openPrice', 'closePrice', 'b_low', 'b_high', 'pnl', 'state' ], 
        verbose=1 )
    return pnl, state

def c_s1( highPrice, lowPrice, openPrice, closePrice, b_low, b_high, bp, pnl, state ):
    '''
    with simple positional slippage
    '''
    from scipy.weave import inline_tools
    n = len( highPrice )
    
    for x in ( lowPrice, openPrice, closePrice ):
        assert( n == len( x ))
    
    code='''
      int i=0;
      int ba = 0;
      int sa = 0;
      float r, costs;
      
      for ( i=0; i<n; i++ ) {
        ba = 0;
        sa = 0;
        r = 0;
        if ( ( openPrice[i] - lowPrice[i] ) >= b_low ) {
            ba = 1;
        };
        
        if ( ( highPrice[i] - openPrice[i] ) >= b_high ) {
            sa = 1;
        };
        
        if ( ba && sa ) {
            r        = b_low + b_high;
            costs    = ( ( openPrice[i] - b_low ) + ( openPrice[i] + b_high ) ) * bp;
            
            if ( r > 0 ) { r -= costs; }
            if ( r < 0 ) { r += costs; }
            
            pnl[i] = r;
            state[i] = ba + 10 * sa;
            continue;
        };
        
        if ( ba ) {
            r = closePrice[i] - ( openPrice[i] - b_low );
            costs = ( ( openPrice[i] - b_low ) + closePrice[i] ) * bp;
        };

        if ( sa ) {
            r = ( openPrice[i] + b_high ) - closePrice[i];
            costs = ( ( openPrice[i] + b_high ) + closePrice[i] ) * bp;
        };

        if ( r > 0 ) { r -= costs; }
        if ( r < 0 ) { r += costs; }
        
        pnl[i] = r;
        state[i] = ba + 10 * sa;
        
      };
      return_val=i;
      '''        
    inline_tools.inline( code,
        ['n', 'bp', 'highPrice', 'lowPrice', 'openPrice', 'closePrice', 'b_low', 'b_high', 'pnl', 'state' ], 
        verbose=1 )
    return pnl, state

def c_s3( highPrice, lowPrice, openPrice, closePrice, b_low, b_high, bp, pnl, state, pnlcosts ):
    '''
    with simple positional slippage added to a separate var
    '''
    
    from scipy.weave import inline_tools
    n = len( highPrice )
    
    for x in ( lowPrice, openPrice, closePrice ):
        assert( n == len( x ))
    
    code='''
      int i=0;
      int ba = 0;
      int sa = 0;
      float r, costs;
      
      for ( i=0; i<n; i++ ) {
        ba    = 0;
        sa    = 0;
        r     = 0;
        costs = 0;
        
        if ( ( openPrice[i] - lowPrice[i] ) >= b_low ) {
            ba = 1;
        };
        
        if ( ( highPrice[i] - openPrice[i] ) >= b_high ) {
            sa = 1;
        };
        
        if ( ba && sa ) {
            pnl[i]       = b_low + b_high;
            pnlcosts[i]  = ( ( openPrice[i] - b_low ) + ( openPrice[i] + b_high ) ) * bp;
                        
            state[i] = ba + 10 * sa;
            continue;
        };
        
        if ( ba ) {
            r = closePrice[i] - ( openPrice[i] - b_low );
            costs = ( ( openPrice[i] - b_low ) + closePrice[i] ) * bp;
        };

        if ( sa ) {
            r = ( openPrice[i] + b_high ) - closePrice[i];
            costs = ( ( openPrice[i] + b_high ) + closePrice[i] ) * bp;
        };
        
        pnl[i]      = r;
        pnlcosts[i] = costs;
        state[i]    = ba + 10 * sa;
        
      };
      return_val=i;
      '''
        
    inline_tools.inline( code,
        ['n', 'bp', 'highPrice', 'lowPrice', 'openPrice', 'closePrice', 'b_low', 'b_high', 'pnl', 'state', 'pnlcosts' ], 
        verbose=1 )
    return pnl, pnlcosts, state

def c_s2( highPrice, lowPrice, openPrice, closePrice, b_low, b_high, bp, pnl, state ):
    '''
    with simple share slippage
    '''
    from scipy.weave import inline_tools
    n = len( highPrice )
    
    for x in ( lowPrice, openPrice, closePrice ):
        assert( n == len( x ))
    
    code='''
      int i=0;
      int ba = 0;
      int sa = 0;
      float r, costs;
      
      for ( i=0; i<n; i++ ) {
        ba = 0;
        sa = 0;
        r = 0;
        if ( ( openPrice[i] - lowPrice[i] ) >= b_low ) {
            ba = 1;
        };
        
        if ( ( highPrice[i] - openPrice[i] ) >= b_high ) {
            sa = 1;
        };
        
        if ( ba && sa ) {
            r        = b_low + b_high;
            /* costs    = ( ( openPrice[i] - b_low ) + ( openPrice[i] + b_high ) ); */
            costs    = 2 * bp;
            
            if ( r > 0 ) { r -= costs; }
            if ( r < 0 ) { r += costs; }
            
            pnl[i] = r;
            state[i] = ba + 10 * sa;
            continue;
        };
        
        if ( ba ) {
            r = closePrice[i] - ( openPrice[i] - b_low );
            /* costs = ( ( openPrice[i] - b_low ) + closePrice[i] ) * bp; */
            costs    = 2 * bp;
        };

        if ( sa ) {
            r = ( openPrice[i] + b_high ) - closePrice[i];
            /* costs = ( ( openPrice[i] + b_high ) + closePrice[i] ) * bp; */
            costs    = 2 * bp;
        };

        if ( r > 0 ) { r -= costs; }
        if ( r < 0 ) { r += costs; }
        
        pnl[i] = r;
        state[i] = ba + 10 * sa;
        
      };
      return_val=i;
      '''        
    inline_tools.inline( code,
        ['n', 'bp', 'highPrice', 'lowPrice', 'openPrice', 'closePrice', 'b_low', 'b_high', 'pnl', 'state' ], 
        verbose=1 )
    return pnl, state

def py_s0( highPrice, lowPrice, openPrice, closePrice, b_low, b_high, pnl, state ):
    '''
    '''
    n = len( highPrice )    
    for x in ( lowPrice, openPrice, closePrice ):
        assert( n == len( x ))
    
    for i in xrange( n ):
        ba  = 0
        sa  = 0
        r   = 0
        if ( openPrice[i] - lowPrice[i] ) >= b_low:
            ba = 1

        if ( highPrice[i] - openPrice[i] ) >= b_high:
            sa = 1
        
        if ba and sa:
            pnl[i] = b_low + b_high
            state[i] = ba + 10 * sa
            continue;
        
        if ba:
            r = closePrice[i] - ( openPrice[i] - b_low )
        
        if sa:
            r = ( openPrice[i] + b_high ) - closePrice[i]
      
        pnl[i] = r;
        state[i] = ba + 10 * sa;
        
    return pnl, state

def c_me0( k, highPrice, lowPrice, openPrice, closePrice ):
    '''
    '''
    from scipy.weave import inline_tools

    n = len( highPrice )
    
    for x in ( lowPrice, openPrice, closePrice ):
        assert( n == len( x ))
            
    code='''
      int i=0;
      int j=0;

      for ( i=0; i < n- ( k - 1) ; i++ ) {
        if ( highPrice[i] < closePrice[i] ) {
            highPrice[i] = closePrice[i];
        };

        if ( highPrice[i] < openPrice[i] ) {
            highPrice[i] = openPrice[i];
        };

        if ( lowPrice[i] > closePrice[i] ) {
            lowPrice[i] = closePrice[i];
        };

        if ( lowPrice[i] > openPrice[i] ) {
            lowPrice[i] = openPrice[i];
        };
      
          for ( j=1; j < k; j++ ) {
            if ( lowPrice[i] > lowPrice[i+j] ) {
                lowPrice[i] = lowPrice[i+j];
            };

            if ( lowPrice[i] > closePrice[i+j] ) {
                lowPrice[i] = closePrice[i+j];
            };

            if ( lowPrice[i] > openPrice[i+j] ) {
                lowPrice[i] = openPrice[i+j];
            };
                

            if ( highPrice[i] < highPrice[i+j] ) {
                highPrice[i] = highPrice[i+j];
            };

            if ( highPrice[i] < closePrice[i+j] ) {
                highPrice[i] = closePrice[i+j];
            };

            if ( highPrice[i] < openPrice[i+j] ) {
                highPrice[i] = openPrice[i+j];
            };

          };
      };
      return_val= n - ( k-1 );
      '''
    closePrice[:-k] = closePrice[k:]
    length = inline_tools.inline( code,
        ['n', 'k', 'highPrice', 'lowPrice', 'openPrice', 'closePrice', ], 
        verbose=1 )
    return length

def py_me0( k, highPrice, lowPrice, openPrice, closePrice ):
    '''
    '''
    modelParams = twkval.getenv( 'mdl_params' )
    
    if modelParams and 'calibParams' in modelParams:
        if 'clipType' in modelParams['calibParams' ]:
            clipType = modelParams['calibParams' ][ 'clipType' ]
            if clipType == 'percentHighLow':
                clipPrcntHigh   = modelParams['calibParams' ][ 'clipHigh' ]
                clipPrcntLow    = modelParams['calibParams' ][ 'clipLow'  ]
                highPrice       = drut.clipTop(x=highPrice, prcnt=clipPrcntHigh )
                lowPrice        = drut.clipTop(x=lowPrice, prcnt=clipPrcntLow )
            elif clipType == 'plain':
                pass
            else:
                raise ValueError( 'Unknown clipType = %s' % str( clipType ) )
            
    n = len( highPrice )
    
    for x in ( lowPrice, openPrice, closePrice ):
        assert( n == len( x ))
            
    for i in xrange( n - (k-1) ):
        highPrice[i]    = max( closePrice[i], highPrice[i], openPrice[i] )        
        lowPrice[i]     = min( closePrice[i], lowPrice[i], openPrice[i] )
    
        for j in range( 1, k ):
            lowPrice[i] = min( lowPrice[i],  lowPrice[i+j],  closePrice[i+j], openPrice[i+j] )              
            highPrice[i]= max( highPrice[i], highPrice[i+j], closePrice[i+j], openPrice[i+j] )
    
    if k > 1:
        closePrice[:-(k-1)] = closePrice[(k-1):]
    return n - ( k-1 )

def s0( highPrice, lowPrice, openPrice, closePrice, b_low, b_high, pnl, state):
    '''compat layer'''
    if compat.isweavable():
        return c_s0( highPrice, lowPrice, openPrice, closePrice, b_low, b_high, pnl, state )

    raise ValueError( 'No python implementation yet')

def s1( highPrice, lowPrice, openPrice, closePrice, b_low, b_high, pnl, state, bp):
    '''compat layer'''
    if compat.isweavable():
        return c_s1( 
            highPrice=highPrice, lowPrice=lowPrice, openPrice=openPrice, closePrice=closePrice, 
            b_low=b_low, b_high=b_high, bp=bp, 
            pnl=pnl, state=state )

    raise ValueError( 'No python implementation yet')

def s2( highPrice, lowPrice, openPrice, closePrice, b_low, b_high, pnl, state, bp):
    '''compat layer'''
    if compat.isweavable():
        return c_s2( 
            highPrice=highPrice, lowPrice=lowPrice, openPrice=openPrice, closePrice=closePrice, 
            b_low=b_low, b_high=b_high, bp=bp, 
            pnl=pnl, state=state )

    raise ValueError( 'No python implementation yet')

def s3( highPrice, lowPrice, openPrice, closePrice, b_low, b_high, pnl, state, pnlcosts, bp):
    '''compat layer'''
    
    if compat.isweavable():
        return c_s3( 
            highPrice=highPrice, lowPrice=lowPrice, openPrice=openPrice, closePrice=closePrice, 
            b_low=b_low, b_high=b_high, bp=bp, 
            pnl=pnl, pnlcosts=pnlcosts, state=state )

    raise ValueError( 'No python implementation yet')

def me0( k, highPrice, lowPrice, openPrice, closePrice ):
#    '''compat layer'''
#    if compat.isweavable():
#        return c_me0( k=k, highPrice=highPrice, lowPrice=lowPrice, openPrice=openPrice, closePrice=closePrice )
#    raise ValueError( 'No python implementation yet')
    return py_me0( k=k, highPrice=highPrice, lowPrice=lowPrice, openPrice=openPrice, closePrice=closePrice )

'''
adding order management
'''

def getLimitFills( symbols, boundObj, highLow ):
    openPrice   = highLow[ 'openPrice' ] 
    highPrice   = highLow[ 'highPrice' ]
    lowPrice    = highLow[ 'lowPrice' ]
    closePrice  = highLow[ 'closePrice' ]
    upperLimitFills = { 
        'qty'       : numpy.zeros( len( symbols ) ),
        'price'     : numpy.zeros( len( symbols ) ),
        'symbols'   : symbols,
    }
    lowerLimitFills = copy.deepcopy( upperLimitFills )

    # we have only one open price    
    if boundObj.openPrice() == None:
        boundObj.setOpenPrice( openPrice )
    
    openPrice   = boundObj.openPrice()
    bounds      = boundObj.bounds()
    sid         = boundObj.startSession( )
    
    for ix, ( bound, h, l, o, c ) in enumerate( zip ( bounds, highPrice, lowPrice, openPrice, closePrice ) ):
        low, high = bound
        
        upperLimitFills[ 'price' ][ ix ] = c
        lowerLimitFills[ 'price' ][ ix ] = c
        
        h = max( h, o, c )
        l = min( l, o, c )
        
        if o + high <= h and boundObj.isAvailHighByIx( ix ):
            # pos qty -> reverse, negative qty -> trend
            upperLimitFills[ 'price' ][ ix ] = o + high
            qty = boundObj.takeHighByIx( ix )
            logger.debug( 'getLimitFills: high: ix=%2d up=%5.2f down=%5.2f h=%6.2f l=%6.2f o=%.2f qty=%5d' % ( ix, low, high, h, l, o, qty ) )
            
        if o - low >= l and boundObj.isAvailLowByIx( ix ):
            lowerLimitFills[ 'price' ][ ix ] = o - low
            qty = boundObj.takeLowByIx( ix )
            logger.debug( 'getLimitFills:  low: ix=%2d up=%5.2f down=%5.2f h=%6.2f l=%6.2f o=%.2f qty=%5d' % ( ix, low, high, h, l, o, qty ) )

    ssn = boundObj.endSession( sid ) 
    
    lowerLimitFills[ 'qty' ] = ssn[ 'low' ]
    upperLimitFills[ 'qty' ] = ssn[ 'high' ]
    
    return { 'upperLimitFills': upperLimitFills, 'lowerLimitFills': lowerLimitFills }

def getCloseFills( symbols, qtys, highLow ):
    closePrice  = highLow[ 'closePrice' ]
    closeFills  = { 
        'qty'       : numpy.zeros( len( symbols ) ),
        'price'     : numpy.zeros( len( symbols ) ),
        'symbols'   : symbols,
    }

    for ix, ( c, qty ) in enumerate( zip ( closePrice, qtys ) ):
        if qty == 0:
            continue
        
        closeFills[ 'qty'   ][ ix ] = -qty
        closeFills[ 'price' ][ ix ] =  c
        logger.debug( 'getLimitFills:close: ix=%2d c=%6.2f qty=%5d' % ( ix, c, qty ) )

    return { 'closeFills': closeFills }

def hasFills( f ):
    return sum( numpy.abs( f['qty'] ) )

def managePos( params, symbols, boundObjs, highLow ):
    fills   = []
    holdingPeriod = params[ 'HoldingPeriod' ]
    
    for boundObj in boundObjs:
        lfills  = getLimitFills( symbols=symbols, boundObj=boundObj, highLow=highLow )
    
        for n in ( 'upperLimitFills', 'lowerLimitFills' ):    
            if hasFills( lfills[ n ] ):
                fills.append( lfills[ n ] )

    if len( boundObjs ) > holdingPeriod:
        boundObj= boundObjs.pop( 0 )
        qtys    = boundObj.takePositions()
        cfills  = getCloseFills( symbols=symbols, qtys=qtys, highLow=highLow )
        
        for n in ( 'closeFills', ):    
            if hasFills( cfills[ n ] ):
                fills.append( cfills[ n ] )
    
    return fills
