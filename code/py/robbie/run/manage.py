import sys

import meadow.run.util as run_util
from   optparse import OptionParser
import meadow.tweak.value as twkval
import meadow.lib.winston as winston

usage = '''usage:

    %prog -t tradedate -s strategy -m sim-seed -p split
    
    %prog -t 20130103 -s BULDOG_V1 -m sim-seed -p split -b

'''

def run( calibDate, strategyName, opMode, operation ):
    dataName     = 'CachedCalibs'
    if operation == 'split':
        exists, dirName = winston.pathCached( 
                        mode         = opMode, 
                        strategyName = strategyName, 
                        calibDate    = calibDate, 
                        dataName     = dataName, 
                        createDir    = False )
        if not exists:
            raise ValueError( 'No such dir=%s' % dirName )
        
        fileName = winston.fileNameCached( dirName=dirName, dataName=dataName )
        options = { 'ThrowIfOverride' : False }         
        run_util.dumpVars( dirName=dirName, fileName=fileName, options=options )

if __name__ == '__main__':
    
    parser = OptionParser( usage=usage, version='%prog 1.0' )
    parser.add_option('-t', '--tradedate',  action='store',     dest='tradedate',   type='str'      )    
    parser.add_option('-s', '--strategy',   action='store',     dest='strategy',    type='str'      )    
    parser.add_option('-b', '--instarbucks',action='store_true',dest='instarbucks', default=False   )
    parser.add_option('-a', '--amend',      action='store',     dest='amend',       default=None    )
    parser.add_option('-p', '--op',         action='store',     dest='operation',   default=None    )    
    parser.add_option('-m', '--mode',       action='store',     dest='mode',        default=None    )    
    
    (options, args) = parser.parse_args()

    if args:
        print 'bad args', args
        sys.exit()
        
    if options.instarbucks:
        print 'inStarbucks!'
        twkval.setval('env_inStarbucks', True )

    import meadow.strategy.repository as strategyrep
    strategyrep.init()

    for name in ( 'tradedate', 'strategy', 'mode', 'operation' ):
        val = getattr( options, name )
        if not val:
            raise ValueError( 'need %s. Currently %s=%s' % ( name, name, val ) )

    run( calibDate=options.tradedate, strategyName=options.strategy, opMode=options.mode, operation=options.operation )