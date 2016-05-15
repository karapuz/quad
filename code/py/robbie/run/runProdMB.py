import sys

import meadow.lib.calendar as cal
import meadow.run.mode as run_mode
from   optparse import OptionParser
import meadow.tweak.value as twkval
import meadow.tweak.util as twkutil
import meadow.tweak.context as twkcx
import meadow.lib.winston as winston
from   meadow.lib.logging import logger
import meadow.lib.debugging as debugging 
import meadow.sim.dailyDriverMultiBlock as driver
import meadow.strategy.amendrepository as amendrep
import meadow.sim.util as simutil

usage = '''usage:
general mode 
    %prog -e enddate -s strategy
            -l [will list all strategies]
            -s strategy -p [will list all params and stop]
dev mode:
    %prog -t 20130107 -e 20130108 -s DRAGON_V6 -m dev

sim mode:
    %prog -t 20130107 -e 20130108 -s DRAGON_V6 -m sim

sim-seed mode:
    %prog -t 20130106 -e 20130108 -s DRAGON_V6 -m sim-seed

sim-prod mode:
    %prog -t 20130106 -e 20130108 -s DRAGON_V6 -m sim-prod

modes:
    sim-seed, sim-prod, sim, dev    
'''

def run( mode, amendName, strategyName, endDate, tradeDate ):
    
    if not cal.isbizday( tradeDate ):
        raise ValueError( '%s is not a trade date!' % tradeDate )
    
    import robbie.strategy.repository as strategyrep
    strategyrep.init()
        
    if amendName:
        logName = ( strategyName, amendName, mode )
    else:
        logName = ( strategyName, mode )

    simutil.setLoggerUnderWinston( appName=logName, now=tradeDate )

    strategyInstance, origParams = strategyrep.getStrategy( endDate, strategyName )

    tweaks = {}
    if 'Tweaks' in origParams:
        tweaks.update( origParams[ 'Tweaks'] )
    
    if amendName:
        amendedParams   = amendrep.applyAmend( origParams, amendName )
        fullName        = '%s_%s' % ( strategyName, amendName )
    else:
        amendedParams   = origParams
        fullName        = strategyName
        
    if amendName:
        logger.debug( 'amendedParams: %s' % str( amendedParams ) )
    
    amendrep.logAmends( 
        strategyName    = strategyName, 
        stratParams     = origParams, 
        amendName       = amendName, 
        amendedParams   = amendedParams )

    # please consult with the winston documents for the description of the modes    
    if mode not in run_mode.allModes():
        raise ValueError( 'Unknown mode %s' % mode )
    
    # sim-seed and sim-prod must have tradedate    
    if mode not in ( 'dev' ):
        if not tradeDate:
            raise ValueError( 'Must have tradedate [%s]' % str( tradeDate ) )
    
    tradeDate = int( tradeDate ) if tradeDate else cal.today()
    
    tweaks[ 'debug_level'  ] = debugging.LEVEL_LOW  
    tweaks[ 'run_mode'     ] = mode
    tweaks[ 'run_tradeDate'] = tradeDate
        
    with twkcx.Tweaks( **tweaks ):        
        twkutil.showProdVars()
        
        return driver.run(
                strategyInstance = strategyInstance, 
                params           = amendedParams, 
                fullName         = fullName )

if __name__ == '__main__':
    
    parser = OptionParser( usage=usage, version='%prog 1.0' )
    parser.add_option('-e', '--enddate',    action='store',     dest='enddate',     type='int'      )    
    parser.add_option('-t', '--tradedate',  action='store',     dest='tradedate',   type='str'      )    
    parser.add_option('-s', '--strategy',   action='store',     dest='strategy',    type='str'      )    
    parser.add_option('-b', '--instarbucks',action='store_true',dest='instarbucks', default=False   )
    parser.add_option('-m', '--mode',       action='store',     dest='mode',        default=None    )    
    parser.add_option('-a', '--amend',      action='store',     dest='amend',       default=None    )
    parser.add_option('-j', '--slippage',   action='store',     dest='slippage',    default=None    )
    parser.add_option('-n', '--simname',    action='store',     dest='simname',     default=None    )
    parser.add_option('-r', '--regime',     action='store',     dest='regime',      default=None    )
    parser.add_option('-c', '--cachemode',  action='store',     dest='cachemode',   default='local' )
    parser.add_option('-o', '--posmon',     action='store',     dest='posmon',      default=None )
    
    (options, args) = parser.parse_args()

    if args:
        print 'bad args', args
        sys.exit()
        
    if options.instarbucks:
        twkval.setval('env_inStarbucks', True )

    if options.cachemode:
        twkval.setval('env_cacheType', options.cachemode )

    for attr in ( 'enddate', 'strategy', 'mode' ):
        if not getattr( options, attr ):  
            raise ValueError( 'Must have attr [%s,%s]' % ( attr, getattr( options, attr ) ) )

    tweaks = {}
    if options.posmon:
        tweaks[ 'sim_posMon'] = options.posmon
    
    if options.slippage:
        slippageType, slippageData = options.slippage.split(',')
        tweaks[ 'sim_marketSlippage' ] = ( slippageType, slippageData )

    if options.regime:
        tweaks[ 'dev_regime' ] = options.regime
    
    if not options.simname:
        logger.warn('simname not set. Results will not be saved.')
    else:
        pklFname = winston.getStorageRoot( options.strategy, options.simname )
        logger.info('will save results in %s' % pklFname)
        
    with twkcx.Tweaks( **tweaks ):        
        stratInst, specProcData, posmon = run( 
             mode           = options.mode, 
             strategyName   = options.strategy,
             amendName      = options.amend, 
             endDate        = options.enddate,
             tradeDate      = options.tradedate,
             )
    
    if options.simname and options.mode == 'sim':
        posmon.storePosData( pklFname )
        logger.info('Saved results in %s' % pklFname)
    