import sys
import numpy

import meadow.lib.calendar as cal
from   optparse import OptionParser
import meadow.tweak.context as twkcx
import meadow.lib.winston as winston
from   meadow.lib.logging import logger
import meadow.strategy.repository_util as repo_util

def createInitialKeysFromProd( tradeDate=20130318, opMode='sim-prod', stratName='EQ_US_CSH' ):
    calibDate   = cal.bizday(tradeDate, '-1b')
    data        = winston.loadCached(
        mode          = opMode, 
        strategyName  = stratName, 
        calibDate     = tradeDate, 
        prevCalibDate = calibDate,
        dataName      = 'CachedCalibs' )
    
    logger.debug( 'symbols shape = %s' % str( data[ 'symbols' ].shape ) )
    ports = {}
    ports['CurrPort' ] = numpy.zeros( len( data[ 'symbols' ] ) )
    ports['SODPort'  ] = numpy.zeros( len( data[ 'symbols' ] ) )

    for key in ( 'CurrPort', 'SODPort' ):
        val = ports[ key ]
        winston.addKey( mode=opMode, strategyName=stratName, calibDate=tradeDate, key=key, val=val, override=False )

    if opMode == 'trade-prod':
        fExp        = ()
        override    = False
        with twkcx.Tweaks( run_tag = str( tradeDate ) ):
            winston.storeInitialExposure( fExp, debug=True, override=override )

usage = '''
to add verification exception:
    python meadow/sim/manage.py -s EQ_US_CSH -p verification_exception -a /tmp/a.ex

    where /tmp/a.ex might have:    

    [('ValueDiffer', '::key(CalibParams)::key(Del-rmw)', False, True)]

to verify:
    python meadow/sim/manage.py -s EQ_US_CSH -p verify -m sim-seed

'''

if __name__ == '__main__':
    parser = OptionParser( usage=usage, version='%prog 1.0' )
    parser.add_option('-t', '--tradedate',  action='store',     dest='tradedate',   default=cal.today(),    type='str'      )    
    parser.add_option('-s', '--strategy',   action='store',     dest='strategy',    default=None,           type='str'      )    
    parser.add_option('-m', '--mode',       action='store',     dest='mode',        default=None    )    
    parser.add_option('-p', '--op',         action='store',     dest='operation',   default=None    )    
    parser.add_option('-a', '--args',       action='store',     dest='args',        default=None    )    
    
    (options, args) = parser.parse_args()

    if args:
        print 'bad args', args
        sys.exit()
        
    tradeDate   = int( options.tradedate )
    operation   = options.operation

    if operation == 'init':    
        opMode      = options.mode
        stratName   = options.strategy
        createInitialKeysFromProd( tradeDate=tradeDate, opMode=opMode, stratName=stratName )

    elif options.operation == 'verify':
        stratName   = options.strategy
        endDate     = options.tradedate
        opMode      = options.mode
        
        assert opMode, ' must have opMode!'
        assert stratName, ' must have stratName!'
        
        import meadow.strategy.signature as signature
        import meadow.strategy.repository as strategyrep
        
        strategyrep.init()            
        strategyInstance, params = strategyrep.getStrategy( endDate, stratName )

        loadCacheDate   = cal.bizday( endDate, '-1b' )

        cachedCalib = winston.loadCached(
            mode         = opMode, 
            strategyName = stratName, 
            calibDate    = tradeDate, 
            prevCalibDate= loadCacheDate,
            dataName     = 'CachedCalibs',
            throw        = True )
        
        vExceptions = signature._exceptions
        
        signature.validate( 
            validationName = ( opMode, stratName ), 
            cachedCalib     = cachedCalib, 
            signatureName   = 'ModelSignature', 
            params          = params,
            exceptions      = vExceptions )

        
    elif options.operation == 'verification_exception':
        fileName    = options.args
        strategy    = options.strategy
        if not repo_util.strategyExists(strategy=strategy, load=True):
            names = repo_util.listNames()
            raise ValueError( '%s is not a valid stratgy!\nStrategies: %s' % ( strategy, str( names ) ) )
        
        if not fileName:
            raise ValueError( 'Need a file for %s. Got %s' % ( operation, fileName ) )
        if not strategy:
            raise ValueError( 'Need a strategy for %s. Got %s' % ( operation, strategy ) )
        
        with open( fileName, 'rU') as f:
            rawExceptions = eval( f.read() )
            
        exception = []
        for e in rawExceptions:
            typ     = e[0]
            path    = e[1]
            exception.append( ( typ, path ) )

        exception_  = winston.loadVerificationExceptions( debug=True, throw=False )
        exception_  = exception_ if exception_ else {}

        override    = True
        exception_.update( {strategy: exception} )
        winston.storeVerificationExceptions( exception=exception_, debug=True, override=override )
        exception   = winston.loadVerificationExceptions( debug=True )
        
        for s in exception_:
            for i,e in enumerate( exception[s] ):
                logger.debug( 'ev: %20s %2d %s' % ( s, i, e ) )
                
    else:
        raise ValueError( 'Unknown operation=%s' % options.operation )
