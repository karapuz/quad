import csv
import time
import threading
import meadow.lib.izzy as izzy
import meadow.tweak.value as twkval
import meadow.lib.winston as winston
import meadow.allocation.util as alut
from   meadow.lib.logging import logger
from   meadow.lib.symbChangeDB import symbDB
import meadow.lib.vendortranslation as vtran

'''

a command is a dict

command = {
'TYPE': 'ManualExecution',
'PARAMS': data
}

'''

def tradeThroughStandalone( cmd ):
    import meadow.argus.strattask as strattask
     
    params      = cmd[ 'PARAMS' ] 
    stratName   = params[ 'StratName' ]
    sharesInfo  = params[ 'SharesInfo' ]
    algoSpecs   = params[ 'AlgoSpecs' ]
    tradeDate   = twkval.getenv( 'run_tradeDate' )
    
    return strattask.tradeThroughStandalone( stratName, sharesInfo, tradeDate, algoSpecs )

def processCommand( cmd ):
    typ = cmd[ 'TYPE' ]
    if typ == 'TradeThroughStandalone':
        tradeThroughStandalone( cmd )
    else:
        raise ValueError( 'Unknown typ=%s for cmd=%s' % ( str( typ ), str( cmd ) ) )

def runner( flag, sleepInterval=10 ):
    
    def run_():
        debug       = True
        
        while flag.cont:
            time.sleep( sleepInterval )
            for name in winston.listTradeCommand( debug=False ):
                try:
                    cmd = winston.loadTradeCommand( name=name, debug=debug )
                    winston.consumeTradeCommand( name=name, debug=debug )
                    processCommand( cmd )
                    logger.debug( 'runcommand: processed %s' % str( name ) )
                except:
                    flag.cont = False
                    import traceback
                    logger.error( 'runcommand: failed processing %s' % str( name ) )
                    logger.error(  traceback.format_exc() )
        
    t = threading.Thread( target=run_ )
    t.daemon = True
    t.start()

def _createCommand():
    sharesInfo = { 
        'TradeSymbols'  : [   1,  2 ], 
        'TradeShares'   : [ 100, -200 ], 
    }
    
    cmd = {
    'TYPE'       : 'TradeThroughStandalone',
    'PARAMS'     : 
        {
            'StratName'     : 'EQ_US_CSH',
            'SharesInfo'    : sharesInfo,
            'AlgoSpecs'     : ( 'TWLR_TWAP_MV_TE', 2*57., 5. )
        }
    }
    debug    = True
    override = True
    winston.storeTradeCommand( value=cmd, override=override, debug=debug )

    # cmd1 = winston.loadTradeCommand( debug=debug )

_header = [ 'Inv Date', 'Fund', 'Strategy', 'ticker', 'End Amount' ]
_header = [ e.lower() for e in _header ]

def createCommand( typ='ClosePos', algoSpecs=None, throws=True, debug=True ):
    fp      = izzy.getArgusCommands( typ=typ )
    runDate = twkval.getenv( 'run_tag' )
    runDate = int( runDate )

    reader  = csv.reader(open(fp, 'rb') )
    header  = reader.next()
    header = [ e.lower() for e in header ]

    tix     = header.index( 'ticker'        )
    dix     = header.index( 'inv date'      )
    fix     = header.index( 'fund'          )
    six     = header.index( 'strategy'      )
    eix     = header.index( 'end amount'    )

    allCmds = []
    inst_   = None
    cmd     = None
    
    algoSpecs = algoSpecs if algoSpecs else ( 'TWLR_TWAP_MV_TE', 57., 1. )
    
    if debug:
        logger.debug('createCommand fp=%s' % str( fp ) )

    for cells in reader:
        strat   = cells[ six ]
        fund    = cells[ fix ]
        ticker  = cells[ tix ]
        inst    = alut.instanceByStratFund( strat=strat, fund=fund )
        msymbol = vtran.bloombergSymb2MeadowSymb( symbStr=ticker, includeCountry=True, includeEquity=True )
        mid     = symbDB.symb2MID( symb=msymbol, date=runDate )

        qty = int( cells[ eix ] )
        if qty == 0:
            msg = 'zero qty for symbol=%s for date=%s' % ( ticker, runDate )
            logger.error( msg )
            continue
            
        if typ == 'ClosePos':
            qty = -qty
                    
        if mid < 0:
            msg = 'Bad symbol=%s qty=%s for date=%s' % ( ticker, qty, runDate )
            if throws:
                raise ValueError( msg )
            else:
                logger.error( msg )
                continue
        
        _ivDate = cells[ dix ]
        
        newCmd  = False
        
        if inst_ == None:
            newCmd  = True
        else:
            if inst != inst_:
                newCmd = True
            else:
                newCmd = False
                
        if newCmd:
            inst_ = inst
            sharesInfo = { 
                'TradeSymbols'  : [], 
                'TradeShares'   : [], 
            }
            
            cmd = {
            'TYPE'       : 'TradeThroughStandalone',
            'PARAMS'     : 
                {
                    'StratName'  : inst,
                    'SharesInfo' : sharesInfo,
                    'AlgoSpecs'  : algoSpecs,
                }
            }            
            allCmds.append( cmd )                

        cmd[ 'PARAMS' ][ 'SharesInfo'][ 'TradeSymbols' ]    += [ mid ]
        cmd[ 'PARAMS' ][ 'SharesInfo'][ 'TradeShares' ]     += [ qty ]
        
        if debug:
            logger.debug( 'createCommand: new line=%s' % str( ( inst, ticker, mid, qty ) ) )

    if debug:
        logger.debug( 'createCommand: allCmds=%s' % str( allCmds ) )
        
    for cmd in allCmds:    
        debug   = True
        override= True
        inst    = cmd[ 'PARAMS' ][ 'StratName' ]
        winston.storeTradeCommand( name=inst, value=cmd, override=override, debug=debug )


