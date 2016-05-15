import numpy
import datetime
import threading

import meadow.tweak.util as twkut
import meadow.tweak.context as twkcx
import meadow.lib.logging as logging
import meadow.lib.report as libreport
import meadow.argus.util as argusutil
import meadow.argus.bbgtask as bbgtask
import meadow.lib.datetime_util as dut
from   meadow.lib.logging import logger
import meadow.lib.journalling as journalling

def startBbgBobJob( bobArgs=None, startJrnl=True, final=datetime.time( 16, 1 ) ):
    
    streamBlock = []    
    flag        = argusutil.Flag( True )
    create      = startJrnl
    jrnlRoot    = journalling.getJournalRoot( create=create )
    
    tweaks = { 
        'jrnl_root'     : jrnlRoot,
        'bbgp_space'    : journalling.jrnl_space 
    }
    logger.debug( 'startJrnl=%s jrnlRoot=%s' % ( startJrnl, jrnlRoot ) )
        
    with twkcx.Tweaks( **tweaks ):
        
        logger.debug('startBbgBobJob %s' % ( 'init' ) )
        twkut.showProdVars()
        
        marketData = argusutil.newMarketData( readOnly=False, create=True )
        
        run     = bbgtask.createBBGRun( marketData, flag, streamBlock, debug=True )
        runner  = threading.Thread( target=run )
        runner.start()
        
        prevPeriodMD = {} 
        for cumKey in ( 'CUM_TRADE', 'TRADE_QUOTE_COUNT' ):
            prevPeriodMD[ cumKey ] = [ 
                numpy.zeros( marketData[ cumKey ][0].shape ),
                numpy.zeros( marketData[ cumKey ][1].shape )
            ]

        def functor( timeTag, strTime ):
            ttag = dut.secToTime( timeTag )
            journalling.write( md=marketData, prevPeriodMD=prevPeriodMD, ttag=ttag, typ='pkl' )
            for cumKey in ( 'CUM_TRADE', 'TRADE_QUOTE_COUNT' ):
                prevPeriodMD[ cumKey ][0][:] = marketData[ cumKey ][0]
                prevPeriodMD[ cumKey ][1][:] = marketData[ cumKey ][1]

        startTime   = '09:29'
        stopTime    = '16:01'

        # final = datetime.time( 16, 1 )
        logger.debug( 'bbg is started')
        while runner.is_alive(): 
            now = datetime.datetime.now().time()
            if final < now:
                flag.cont   = False
                logger.debug( 'bbg is finished')
                break
            
            if startJrnl:    
                logger.debug( 'journalling is started')
                journalling.schedSingleThread( functor=functor, startTime=startTime, stopTime=stopTime ) 
                flag.cont   = False
                logger.debug( 'journalling is finished')
                logger.close()                
                names, pipes, pipe = streamBlock
                bbgtask._terminate( names, pipes, pipe )
                libreport.kill('Shutting down bbg')
            else:
                logger.debug( 'bbg is alive')
                runner.join( timeout=60 )

        names, pipes, pipe = streamBlock
        bbgtask._terminate( names, pipes, pipe )
        logger.debug( 'falling through')
        logger.close()
        libreport.kill('Shutting down bbg')

if __name__ == '__main__':
    import sys
    from   optparse import OptionParser
    import meadow.lib.config as libconf
    
    parser = OptionParser()
        
    parser.add_option('-g', '--tag',    action="store",         default=None,   dest='run_tag'  )
    parser.add_option('-T', '--turf',   action="store",         default=None,   dest='turf'     )
    parser.add_option('-j', '--jrnl',   action="store_true",    default=False,  dest='jrnl'     )
    parser.add_option('-n', '--night',  action="store_true",    default=False,  dest='night'    )

    (options, args) = parser.parse_args()

    logger.debug( '>>> args = %s' % str( args ) )

    if args:
        libreport.reportAndKill( txt='Unknown options=%s' % str( args ), subject='Process is killed', sendFrom=None, sendTo=None )

    if not options.turf:
        libreport.reportAndKill( txt='Must have turf specified', subject='Process is killed', sendFrom=None, sendTo=None )

    turf        = options.turf
    if not libconf.exists( turf ):
        logger.error('Must have valid turf. Turf "%s" does not exist' % str( turf ) )
        sys.exit()

    tweaks = { 
        'run_turf'  : turf,
    }

    with twkcx.Tweaks( **tweaks ):
        logging.toFile( 'bbg', mode='p' )
        if options.night:
            startBbgBobJob( startJrnl=options.jrnl, final = datetime.time( 22, 1 ) )
        else:
            startBbgBobJob( startJrnl=options.jrnl  )
