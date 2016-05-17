import os
import numpy
import cPickle as pickle
import robbie.util.context as cx
import robbie.util.nxcore as nxcore
from   optparse import OptionParser
import robbie.util.environment as environment
from   robbie.util.logging import logger

names = ( 'symbStr', 'time', 'type', 'ask', 'bid', 'trade', 'ask_size', 'bid_size', 'trade_size' )
# ('eAAPL', 28705000, 1, 476.34000000000003, 476.10000000000002, 0.0, 1, 2, 0)
# ('eAAPL', 28767000, 3, 0.0, 0.0, 476.22000000000003, 0, 0, 200)

def extract( procDate, symbols, create=True  ):        
    _six = names.index( 'symbStr' )
    xix  = names.index( 'time' )
    tix  = names.index( 'type' )
    
    aix  = names.index( 'ask' )
    bix  = names.index( 'bid' )
    rix  = names.index( 'trade' )

    asix = names.index( 'ask_size' )
    bsix = names.index( 'bid_size' )
    rsix = names.index( 'trade_size' )

    with cx.Timer( 'loading' ) as t:
        dictList = nxcore.processFullTapeAsDictList( procDate=procDate, symbols=symbols )
    print 'Done', t.elapsed()
    
    for symbol in symbols:
        root = environment.getSymbolTickPath( symbol=symbol, procDate=procDate, scanChildren=False, stripPath=False )
        if not os.path.exists( root ):
            if create:
                os.makedirs( root )
                logger.debug( 'creating %s' % root )
            else:
                raise ValueError( 'Does not exist %s' % root )
        else:
            logger.debug( 'storing in %s' % root )
        
        if symbol not in dictList:
            logger.error('symbol %s is not present' % symbol )
            continue
              
        data = dictList[ symbol ]
        
        qMat = []
        tMat = []
        with cx.Timer( 'processing' ) as t:
            for line in data:
                typ  = line[ tix  ]
                if typ == 3:
                    r = [ line[ xix ], line[ rix ], line[ rsix ] ]
                    tMat.append( r )
                elif typ == 1:
                    q = [ line[ xix ], line[ aix ], line[ asix ], line[ bix ], line[ bsix ] ]
                    qMat.append( q )
        print 'Done', t.elapsed()
    
        qMat = numpy.array( qMat )
        tMat = numpy.array( tMat )
    
        with open( os.path.join( root, 'quote.pkl' ), 'wb' ) as fd:
            pickle.dump( qMat, fd, pickle.HIGHEST_PROTOCOL )
        with open( os.path.join( root, 'trade.pkl' ), 'wb' ) as fd:
            pickle.dump( tMat, fd, pickle.HIGHEST_PROTOCOL )
    
if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option('-t', '--tag',  action='store', default=None, dest='tag')
    parser.add_option('-s', '--symbol',  action='store', default=None, dest='symbol')
    (options, args) = parser.parse_args()

    if options.tag == None:
        raise ValueError( 'No tag!')

    procDate = str( options.tag )
    symbols = options.symbol.split(',')
    extract( procDate, symbols )    

