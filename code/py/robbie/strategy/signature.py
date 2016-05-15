'''
'''
import meadow.lib.cmp as libcmp
from   meadow.lib.logging import logger

_exceptions = [
    ( 'KeysDiffer',  '::key(CalibParams)' ),
    ( 'ValueDiffer', '::key(GetData)::key(EndDate)' ),
    ( 'ValueDiffer', '::key(GetData)::key(TagName)' ),
]

def validate( validationName, cachedCalib, signatureName, params, debug=True, exceptions=None):
    exceptions  = exceptions if exceptions else _exceptions 
      
    params_ = cachedCalib[ signatureName ]
    ndiff   = []
    diff    = libcmp.diff(params_, params )
    validate_( diff, ndiff, exceptions=exceptions, debug=debug )
    if ndiff:
        raise ValueError( '%s: Calibration does not match with the model %s' % ( str( validationName ), str( ndiff ) ) )

def validate_( diff, ndiff, exceptions, debug ):
    if debug:
        logger.debug( 'validate: diff=%s' % str( diff ) )
    
    for line in diff:
        if isinstance( line, ( tuple, list ) ):
            if line[0] in ( 'KeysDiffer', 'ValueDiffer', 'TypesDiffer' ):
                diffType, diffName, diffVal0, diffVal1 = line
                if ( ( diffType, diffName ) ) in exceptions:
                    continue
                if debug:
                    logger.error( 'signature type=%s' % str( ( diffType, diffName ) ) )
                    logger.error( '          val0=%s' % str( diffVal0 ) ) 
                    logger.error( '          val1=%s' % str( diffVal1 ) ) 
                    
                if line[0] == 'TypesDiffer':
                    ndiff.append( ( diffType, diffName, str( diffVal0 ), str( diffVal1 ) ) )
                else:
                    ndiff.append( ( diffType, diffName, diffVal0, diffVal1 ) )
                    
            else:
                validate_( diff=line, ndiff=ndiff, exceptions=exceptions, debug=debug )
                