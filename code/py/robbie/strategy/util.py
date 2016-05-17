'''
'''
import copy
import numpy
import itertools

from   robbie.util.logging import logger
import robbie.feed.lib.repository as flrepository

def findBlock( keys, typ ):
    ''' find the block specifications '''
    for ( blockType,  blockSpecs ) in keys:
        if blockType == typ:
            return ( blockType,  blockSpecs )
    raise ValueError( 'Can not find Calib block!' )

def conv2D( t ):
    ''' convert to 2d tuple struct. Used mostly as a convenience func for path creating '''
    if isinstance( t, tuple ):
        return tuple( zip( t ) )
    else:
        return zip( t )

def replicate( params ):
    ''' replicate strategy parameters '''
    return copy.deepcopy( params )

def amend( params, name, value ):
    ''' amend strategy parameters '''
    if isinstance( name, str ):
        if isinstance( value, dict ):
            for subName, subValue in value.iteritems():
                params[ name ][ subName ] = subValue
        else:
            params[ name ] = value
        return params
    
    if isinstance( name, ( tuple, list ) ):
        k = params
        for n in name[:-1]:
            print 'n=',n
            if n not in k:
                raise ValueError( 'key=%s is not in params keys=%s' % ( n, k.keys() ))
            k = k[ n ]
        n = name[-1]
        if n not in k:
            raise ValueError( 'key=%s is not in params keys=%s' % ( n, k.keys() ))
        k[ n ] = value

#'RemoveSymbolsRule': ['BADTICKER_TWOINAROW', 'BADTICKER_6HOLES', 'BADTICKER_BEGEND'], 
#'PatchRule': ['PATCH_ONEMISSING']

_valueNames2Shorts = {
    'BADTICKER_TWOINAROW'   : '2inarow',
    'BADTICKER_6HOLES'      : '6holes',
    'BADTICKER_BEGEND'      : 'firstlast',
    'PATCH_ONEMISSING'      : 'p1m',
}

def flatten( vals ):
    ret = []
    for v in vals:
        if isinstance( v, ( tuple, list ) ):
            ret.extend( itertools.chain( v ) )
        else:
            ret.append( v )
    return ret

def defaultIdTransform( name, params ):
    if name in params:
        vals    = flatten( params[ name ] )
        return name.lower() + '_'  + '_'.join( _valueNames2Shorts.get( v, v) for v in vals )
    
    if isinstance( name, tuple ):
        vals    = flatten( params[ name ] )
        return name.lower() + '_'  + '_'.join( _valueNames2Shorts.get( v, v) for v in vals )
    
    raise ValueError( 'Do not know hot to interpret name = %s' % str( name ) )

def dataIdParts( dataId, params, ids ):
    return list( 
            itertools.chain( 
                dataId, ( 
                    defaultIdTransform(i, params) 
                        for i in ids if i in params ) ) 
            )

def applyBadTickerRules( colname, origData, rules, debug=False ):
    mat     = origData[ colname     ]
    dates   = origData[ 'dates'     ]
    symbols = numpy.array( origData[ 'symbols'   ] )

    holes   = numpy.array( [ False ] * len( mat[0] ) )
    for ruleName in rules:
        rule    = flrepository.getRule( ruleName )
        h1, mat = rule.execute(colname, dates, mat )
        h1      = h1.ravel()
        holes  += h1
        if debug:
            logger.debug( 'ruleName=%s %s' % ( ruleName, symbols[ h1 == True ] ) )
        
    badSymbols  = symbols[ holes == True    ]
    mat         = mat[:, holes == False     ]
    
    logger.debug( 'TICKER RULEs: badSymbols = %s' % badSymbols )
        
    return holes, badSymbols, mat

def applyPatchRules( mat, colname, origData, rules, debug=False ):
    dates   = origData[ 'dates'     ]

    holes   = numpy.zeros( len( mat[0] ) )
    for ruleName in rules:
        rule    = flrepository.getRule( ruleName )
        h1, mat = rule.execute(colname, dates, mat )
        holes   += h1
        if debug:
            logger.debug( 'ruleName=%s %s' % ( ruleName, sum ( h1 ) ) )
            
    logger.debug( 'PATCH RULEs: holes = %s' %  sum( holes ) )       
    return holes, mat

def calendarCount( trgrData, dates, offset=0, retTyp='int' ):
    typ, data = trgrData
    d = len( dates ) - offset
    
    if d < 0:
        raise ValueError( 'Difference can not be negative %s' % str( ( trgrData, dates, offset ) ) )
    
    if typ == 'bizday':
        n = int( data )
        if retTyp == 'int':
            return n * ( d / n )
        elif retTyp == 'date':
            ix = offset + n * ( d / n )
            return dates[ ix-1 ]
        else:
            raise ValueError( 'Unknown return type = %s %s' % ( str(retTyp), str(data) ) )
    else:
        raise ValueError( 'Unknown trigger type = %s %s' % ( str(typ), str(data) ) )
    
def doNothing( *x ):
    ''' null sink. do not do anything '''
    pass

def doPassthrough( *x ):
    ''' pass-through sink. '''
    return x
