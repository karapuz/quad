import sys

import meadow.sim.util as simutil
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

usage = '''usage:
general mode 

sim-prod mode:
    %prog -t 20130106 -e 20130108 -s DRAGON_V6 -m sim-prod

modes:
    sim-seed, sim-prod, sim, dev    
'''

def run( mode, strategyName, endDate, tradeDate ):
    
    if not cal.isbizday( tradeDate ):
        raise ValueError( '%s is not a trade date!' % tradeDate )
    
    simutil.setLoggerUnderWinston( appName='runSimMode-%s' % mode, now=tradeDate )

    tweaks = {}
        
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
    
    (options, args) = parser.parse_args()

    if args:
        print 'bad args', args
        sys.exit()
        
    if options.instarbucks:
        twkval.setval('env_inStarbucks', True )

    for attr in ( 'enddate', 'strategy', 'mode' ):
        if not getattr( options, attr ):  
            raise ValueError( 'Must have attr [%s,%s]' % ( attr, getattr( options, attr ) ) )

    tweaks = {}
        
    with twkcx.Tweaks( **tweaks ):        
        run( 
             mode           = options.mode, 
             strategyName   = options.strategy,
             endDate        = options.enddate,
             tradeDate      = options.tradedate,
             )
    