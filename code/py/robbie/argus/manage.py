'''
manage argus activities
'''
import sys
import cPickle as pickle

import meadow.lib.calendar as cal
import meadow.tweak.value as twkval
from   optparse import OptionParser
import meadow.lib.winston as winston
import meadow.argus.manageutil as mutil
import meadow.lib.journalling as journalling
import meadow.sanitycheck.strategy as sanstrat
import meadow.strategy.repository as strrep

import meadow.lib.tmp as libtmp
import meadow.lib.logging as logging
from   meadow.lib.logging import logger

usage = '''
check today's journal
    python meadow/argus/manage.py -p check-jrnl

check journal for some other day
    python meadow/argus/manage.py -p check-jrnl -g 20130124

check journal for some other day, and for a specific slice 110600 (11:06)
    python meadow/argus/manage.py -p check-jrnl -g 20130124 -a 110600

dump a slice
    python meadow/argus/manage.py -p dump-ttag -a 121700

sched to run a model today:
    python meadow/argus/manage.py -p sched-model -a DRAGON_V6,BULDOG_V1

validate today's models:
    python meadow/argus/manage.py -p valid-model

dry-run today's models:
    python meadow/argus/manage.py -p dryrun-model

initiate models for a trade date ( -t 20130107 ) with data from ( -g 20130108 ) in starbucks mode (-b)
    python meadow/argus/manage.py -p dryrun-model -g 20130108 -b -t 20130107

populate sod positions from tradar:
    python meadow/argus/manage.py -p sod-tradar

check-ready:
    python meadow/argus/manage.py -p check-ready

augment sim-seed numerical key:
    python meadow/argus/manage.py -p add-num-key -a mode,strategy,date,key,val

augment sim-seed with a py-eval'ed key:
    python meadow/argus/manage.py -p add-py -a mode,strategy,date,key,fileName

dump a key from CachedCalibs into a pickle file:
    python meadow/argus/manage.py -p dump-key -a sim-seed-perse,EQ_US_CSH,20130506,symbols,/tmp/a.pkl

check sim-seed augment key:
    python meadow/argus/manage.py -p check-key -a mode,strategy,date,key

close positions via ArgusCommand:
    python meadow/argus/manage.py -p argus-close -a TWLR_TWAP_MV_TE,500,1

'''

def run( op, args=None, override=False, gui=False, debug=True ):
    
    if op == 'dump-ttag':
        dn  = libtmp.getTempMidDir( app='jrnl_' )
        journalling.dumpTTagAsCsv( ttag=args, dn=dn )

    elif op == 'check-jrnl':
        args = args.split(',') if args else None
        keys, stats = journalling.getTTagStats( args )
        print keys
        for row in stats:
            ttag = row[0]
            vals = row[1:]
            print ttag, vals

    elif op in ( 'add-num-key', 'check-key', 'add-py', 'dump-key' ):
        args = args.split(',')

        if op == 'add-num-key':
            if len( args ) < 5:
                raise ValueError( 'Too few values in %s' % str( args ) )

        elif op == 'check-key':
            if len( args ) < 4:
                raise ValueError( 'Too few values in %s' % str( args ) )
            
        elif op == 'add-py':
            if len( args ) < 5:
                raise ValueError( 'Too few values in %s' % str( args ) )
            
        elif op == 'dump-key':
            if len( args ) < 5:
                raise ValueError( 'Too few values in %s' % str( args ) )

        else:
            raise ValueError( 'Unknown op=%S' % str( op ) ) 

        targetMode      = args[0]
        strategyName    = args[1]

        strrep.reinit()        
        if not strrep.strategyExists( strategyName ):
            raise ValueError( 'Strategy %s does not exists!' % strategyName )
        
        calibDate   = int( args[ 2 ] )
        key         = args[ 3 ]
        override    = True
        # checkMode   = 'sim-seed-perse'
        dataName    = 'CachedCalibs'
        
        if not winston.hasKey( mode=targetMode, strategyName=strategyName, calibDate=calibDate, key=key, debug=False ):
            logger.debug( '%s: %s no augment key' % ( targetMode, str( key ) ) )
        
        if op != 'add-py':
            pCalibDate  = cal.bizday( calibDate, '-1b' ) 
            cc          = winston.loadCached(
                            mode         = targetMode, 
                            strategyName = strategyName, 
                            calibDate    = calibDate, 
                            prevCalibDate= pCalibDate, 
                            dataName     = dataName, debug=False, throw=False)
            if not cc:
                logger.debug( '%s: no data exists' % dataName )
                return
                
            if key not in cc:
                logger.debug( '%s: %s no such key' % ( targetMode, str( key ) ) )
            else:
                logger.debug( '%s: has %s=%s' % ( targetMode, str( key ), str( cc[ key ] ) ) )

        if op == 'dump-key':
            fp          = args[ 4 ]
            val         = cc[ key ]
            override    = True
            with open( fp, 'wb' ) as fd:
                pickle.dump( val, fd )

            logger.debug( '%s dumping to %s %s=%s' % ( targetMode, fp, str( key ), str( val ) ) )

        if op == 'add-num-key':
            val         = float( args[ 4 ] )
            override    = True
            winston.addKey( mode=targetMode, strategyName=strategyName, calibDate=calibDate, key=key, val=val, override=override )
            logger.debug( '%s Added %s=%s' % ( targetMode, str( key ), str( val ) ) )

        elif op == 'add-py':
            fp          = args[ 4 ]
            with open( fp, 'rU') as f:
                val = eval( f.read() )
            override    = True
            winston.addKey( mode=targetMode, strategyName=strategyName, calibDate=calibDate, key=key, val=val, override=override )
            logger.debug( '%s Added %s=%s' % ( targetMode, str( key ), str( val ) ) )
        
    elif op == 'check-mode':
        if not args:
            print 'need to have models specified in -a'
            sys.exit()
            
        stratNames  = args.split(',')
        tradeDate   = twkval.getenv( 'run_tradeDate' )
        prevCalibDate = cal.bizday(tradeDate, '-1b')
        
        results = []
        for stratName in stratNames:
            for mode in ( 'sim-seed', 'trade-prod' ):
                cc = winston.loadCached( mode=mode, strategyName=stratName, calibDate=tradeDate, prevCalibDate=prevCalibDate, dataName='CachedCalibs', debug=False, throw=False )
                status = 'GOOD' if cc else 'BAD '
                results.append( ( cc, status, stratName, mode, tradeDate ) )

        print '\n'        
        for ( cc, status, stratName, mode, tradeDate ) in results:
            print '%s strategy: %12s mode: %8s trade: %s' % ( status, stratName, mode, tradeDate )

    elif op == 'sched-model':
        if not args:
            print 'need to have models specified in -a'
            sys.exit()
            
        models = args.split(',')
        cantRun, nonMBSched, nonMBBase, noAlloc = sanstrat.run( allModels=models )
        
        for name, blob in zip( 
                        ( 'cantRun', 'nonMBSched', 'nonMBBase', 'noAlloc' ),
                        ( cantRun, nonMBSched, nonMBBase, noAlloc ) 
                    ):
            if blob:
                raise ValueError( '%s %s' % ( name, str( blob) ) )
        tradeDate = twkval.getenv( 'run_tradeDate' )
        if not tradeDate:
            tradeDate = twkval.getenv( 'run_tag' )
        
        with twkcx.Tweaks( run_tag=str( tradeDate ) ):
            winston.schedModels( models, override=override, debug=True )

    elif op == 'valid-model':
        
        allModels = winston.getModels( debug=True )
        cantRun, nonMBSched, nonMBBase, noAlloc = sanstrat.run(allModels=allModels)
        
        for name, blob in zip( 
                        ( 'cantRun', 'nonMBSched', 'nonMBBase', 'noAlloc' ),
                        ( cantRun, nonMBSched, nonMBBase, noAlloc ) 
                    ):
            if blob:
                print name, blob
                
    elif op == 'dryrun-model':
        import meadow.argus.strattask as strattask
        endDate     = twkval.getenv( 'run_tag' )
        tradeDate   = twkval.getenv( 'run_tradeDate', throwIfNone=True )
        strattask.initStrategy( endDate, tradeDate )

    elif op == 'sod-tradar':        
        tweaks = twkutil.allTweaks()
        mutil.sodTradarWithTweaks( override=override, tweaks=tweaks, debug=debug )
    
    elif op == 'check-ready':
        tweaks      = twkutil.allTweaks()
        allChecks   = mutil.checkReadyWithTweaks( tweaks )
        mutil.prettyPrintChecks( allChecks )

    elif op == 'argus-close':
        import meadow.argus.runcommand as runcmd
        if args:
            args = args.split(',') if args else None
            algoSpecs = args[0], float( args[1]), float( args[2])
        else:
            algoSpecs = None
        runcmd.createCommand( typ='ClosePos', algoSpecs=algoSpecs )
        
    else:
        raise ValueError( 'Unknown op=%s' % op )

if __name__ == '__main__':
    parser = OptionParser( usage=usage )
    today = cal.today()
    
    parser.add_option('-d', '--debug',      action='store_true',default=False,  dest='debug'        )
    parser.add_option('-b', '--instarbucks',action='store_true',default=False,  dest='instarbucks'  )
    parser.add_option('-p', '--op',         action='store',     default=None,   dest='operation'    )    
    parser.add_option('-g', '--tag',        action='store',     default=today,  dest='tag'          )
    parser.add_option('-a', '--args',       action='store',     default=None,   dest='args'         )
    parser.add_option('-t', '--tradedate',  action='store',     default=today,  dest='tradedate'    )
    parser.add_option('-r', '--override',   action='store_true',default=None,   dest='override'     )
    parser.add_option('-u', '--gui',        action='store_true',default=False,  dest='gui'          )

    logging.toFile('manage_argus_', mode='p' )
    
    (options, args) = parser.parse_args()

    op   = options.operation
    if not op:
        logger.error('Must have an operation!')
        sys.exit()
    
    if options.instarbucks:
        twkval.setval('env_inStarbucks', True )
        
    args = options.args
    run_tag  = str( options.tag )    
    tradeDate= options.tradedate

    jrnlRoot = journalling.getJournalRoot( today=run_tag, create=False )    
    tweaks = {
      'jrnl_root': jrnlRoot, 
      'run_tag': run_tag, 
      'run_tradeDate': int( tradeDate ),
    }
    
    import meadow.tweak.util as twkutil
    import meadow.tweak.context as twkcx
    with twkcx.Tweaks( **tweaks ):
        twkutil.showProdVars( tweaks )
        run( op=op, args=args, override=options.override, gui=options.gui, debug=options.debug  )
