'''
'''
import numpy
from   meadow.lib.logging import logger
 
def name2parts( blockName ):
    ''' split block name into parts '''
    
    parts = blockName.split('-')
    if len( parts ) < 2:
        return None, None
    
    return parts[0], tuple( parts[1:] )

def checkDatesAndSymbols( targetType, specProcData ):
    ''' check dates and symbols in Calib blocks for consistency, and return one set'''
    
    msg     = None                    
    dates   = None
    symbols = None
    
    for blockName, blockData in specProcData.iteritems(): 
        if isinstance( blockName, tuple ):
            blockType, _blockSpecs = blockName[0], blockName[1:]
            if blockType == targetType:
                if dates == None:
                    dates       = blockData[ 'dates'   ]
                    symbols     = blockData[ 'symbols' ]
                    calibName   = blockName
                else:
                    nsymbols= blockData[ 'symbols' ]
                    # ndates  = blockData[ 'dates'   ]

                    symbolDiff = set( symbols ) - set( nsymbols )
                    if symbolDiff:
                        msg = 'symbols for %s do not match! symbolDiff=%s' % ( targetType, str( symbolDiff ) )

                    if msg != None:
                        logger.error( msg )
                        raise ValueError( msg )

    if dates == None:
        msg = 'not dates for calib! %s' % str( dates )
        
    if symbols == None:
        msg = 'no symbols for calib! %s ' % str( symbols )

    if msg != None:
        logger.error( msg )
        raise ValueError( msg )
        
    return calibName

def noShares( sharesInfo ):
    ''' check - no trades are requested '''
     
    if not sharesInfo:
        return True
    
    shares = sharesInfo[ 'TradeShares' ]
    
    if shares == None:
        return True
    
    if isinstance( shares, ( list, numpy.ndarray ) ):
        return sum( abs(s) for s in shares ) == 0
 
    return False
