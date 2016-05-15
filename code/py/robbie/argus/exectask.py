import datetime
import traceback

import meadow.order.twap_2LR_LGCL_MV as twlrtwapmv
import meadow.order.twap_2LR_LGCL_MV_TE as twlrtwapmvte

import meadow.fix.util as fut
import meadow.tweak.value as twkval
import meadow.argus.task as argTask
import meadow.allocation.util as alut
import meadow.argus.util as argusutil
from   meadow.lib.logging import logger
import meadow.argus.schedutil as schedutil 
from   meadow.lib.symbChangeDB import symbDB
import meadow.lib.vendortranslation as vtran

def formTradeSpecs( typ, sym, expName, stratName, amount, targetTime, targetStep ):
    return ( typ, sym, expName, stratName, amount, targetTime, targetStep )

def formAlgoInfo( algoType, targetTime, targetStep ):
        return ( algoType, targetTime, targetStep )

def generateSpecs( stratName, algoInfo, sharesInfo, tradeDate, execSchema ):
    
    typ, targetTime, targetStep = algoInfo
    
    mids    = sharesInfo[ 'TradeSymbols' ]
    shares  = sharesInfo[ 'TradeShares'  ]

    symbols = [ vtran.meadowSymb2BloombergSymb( 
                    symbStr=symbDB.MID2symb( mid, tradeDate ), includeCountry=False, includeEquity=False ) 
                        for mid in mids ]

    sharesInfo[ 'Sym2MID'  ] = dict( ( s,m ) for ( s,m ) in zip( symbols, mids ) ) 

    syms, expNames, amounts = alut.allocNameSymShare( execSchema=execSchema, symbols=symbols, shares=shares )

    tradeSpecs = []
    for sym, expName, amount in zip( syms, expNames, amounts ): 
        if not amount:
            continue
        
        ts = formTradeSpecs( 
            typ=typ, sym=sym, expName=expName, 
            stratName=stratName, amount=amount, 
            targetTime=targetTime, targetStep=targetStep )
                
        tradeSpecs.append( ts )    

    return tradeSpecs
 
def generateOrders( orderManager, orderQueue, tradeSpecs ):
    ''' create an algo trade '''

    algoExp = { 'TWLR_TWAP_MV': {}, 'TWLR_TWAP_MV_TE': {} }    
    simExp  = { 'M': [], 'L': [] }
    
    for line in tradeSpecs:
        typ = line[0]
        
        if typ in algoExp:
            typ, sym, expName, stratName, amount, targetTime, targetStep = line
            
            timeKey = ( targetTime, targetStep )
            
            if timeKey not in algoExp[ typ ]:
                algoExp[ typ ][ timeKey ] = []
            algoExp[ typ ][ timeKey ].append( ( sym, expName, stratName, amount ) )
            
        elif typ in simExp:
            if typ == 'M':
                typ, sym, secType, execVenue, amount = line
                price = 0
                
            elif typ == 'L':
                typ, sym, secType, execVenue, amount, price = line
                
            else:
                raise ValueError( 'Unknown order type=%s for %s' % ( str( type ), str( line ) ) )

            # expName = alut.            
            simExp[ typ ].append( ( typ, sym, secType, execVenue, amount, price ) )
            
        else:
            raise ValueError( 'Unknown type=%s' % typ )
        
    orderExecLink   = orderManager
    relObj          = orderManager.getRelObj()  
    orderType       = 'New'
    
    for typ, timeExp in algoExp.iteritems():
        
        for timeKey, exp in timeExp.iteritems():
            
            ( targetTime, targetStep ) = timeKey
            
            if typ == 'TWLR_TWAP_MV':
                algoObj = twlrtwapmv.TWAP( relObj, orderExecLink, exp, targetTime, targetStep )

            elif typ == 'TWLR_TWAP_MV_TE':
                algoObj = twlrtwapmvte.TWAP( relObj, orderExecLink, exp, targetTime, targetStep )                
            else:
                raise ValueError( 'Unknown algo type=%s' % typ )
                
            data = None
            orderQueue.put( ( typ, orderType, algoObj, data ) )
            
            logger.debug( 'exectask: algo obj: %s' % str( algoObj ) )
            logger.debug( 'exectask: algo order %s generated id=%s' % ( orderType, id( orderQueue ) ) )

    for typ, exp in simExp.iteritems():
        for line in exp:
            ( typ, sym, secType, execVenue, amount, price ) = line
            orderType   = 'New'
            orderId     = orderManager.getOrderId( style='N', instr=sym )
            timeInForce = fut.mapTimeInForce( 'DAY' )  
            
            orderQueue.put( ( typ, orderType, orderId, sym, secType, execVenue, amount, price, timeInForce ) )
            
            logger.debug( 'exectask: qlen=%s simple order %s generated id=%s' % ( orderQueue.qsize(), orderType, id( orderQueue ) ) )
            

nowFunc = datetime.datetime.now
def nowFuncSec():
    dt = nowFunc()
    return dt.hour * 60 * 60 + dt.minute * 60 + dt.second + dt.microsecond / 1e6

def cycleWithArgs( algoObj, marketData ):
    try:
        askPriceSize = marketData[ 'ASK'    ]
        bidPriceSize = marketData[ 'BID'    ]
        
        if algoObj.expired():
            algoObj.finish()
            return
                                    
        algoObj.cycle( nowFuncSec(), bidPriceSize, askPriceSize )
        logger.debug( 'exectask: cycleWithArgs: algo=%s' % str( algoObj ) )
    except:
        logger.error( 'exectask: cycleWithArgs: ALGO FAILED algo=%s' % str( algoObj ) )
        logger.error( traceback.format_exc() )
        algoObj.finish()

def newRunner( orderManager, orderQueue, marketData, flag ):
    ''' create queue runner '''

    # marketData[ 'TRADE'  ]
    askPriceSize = marketData[ 'ASK'    ]
    bidPriceSize = marketData[ 'BID'    ]
    # marketData[ 'SYMBOL' ]         

    logger.debug( 'exectask: newRunner created' )
    def run():
        
        logger.debug( 'exectask: newRunner started' )
        
        while flag.cont:
            logger.debug( 'exectask: newRunner waiting for the request id=%s' % id( orderQueue ) )
            orderData   = orderQueue.get()
            typ         = orderData[0]
            orderType   = orderData[1]
            
            logger.debug( 'exectask: newRunner got request typ=%s' % ( typ ) )
            
            if typ in ( 'M', 'L' ):
                if orderType == 'New':
                    logger.debug( 'exectask: simple order = %s' % str( orderData ) )
                    ( typ, orderType, orderId, sym, secType, execVenue, amount, price, timeInForce ) = orderData
                    expName = ( sym, secType, execVenue )
                    orderManager.sendOrder( orderId=orderId, instr=sym, expName=expName, qty=amount, price=price, timeInForce=timeInForce )
                else:
                    raise ValueError( 'Wrong orderType = %s' % orderType )

            elif typ in ( 'TWLR_TWAP_MV', 'TWLR_TWAP_MV_TE' ):
                if orderType == 'New':
                    (  typ, orderType, algoObj, _data )  = orderData                    
                    currentTime = nowFuncSec()
                    algoObj.start( currentTime )
                    logger.debug( 'exectask: start algoObj=%s' % str( algoObj ) )                    
                    delay       = algoObj.targetStep()
                    maxTime     = currentTime + algoObj.targetTime()

                    def finish():
                        try:
                            algoObj.finish()
                        except:
                            logger.error( 'ALGO FAILED algo=%s' % str( algoObj ) )
                            logger.error( traceback.format_exc() )

                    schedutil.scheduleRepeatAfter( 
                            delay       = delay, 
                            cycleFunc   = cycleWithArgs,
                            finishFunc  = finish, 
                            args        = { 'algoObj': algoObj, 'marketData': marketData }, 
                            logger      =  logger, 
                            firstExec   = False, 
                            flag        = flag, 
                            maxTime     = maxTime,
                            debug       = False,
                    )
                    
                    logger.debug( 'exectask: newRunner scheduled %s' % flag.cont )
                    argusutil.reportMarketDataShape( 'exectask: sched-time', askPriceSize, bidPriceSize )                            
                else:
                    raise ValueError( 'Wrong orderType = %s' % orderType )
            else:
                raise ValueError( 'Wrong type = %s' % typ )

        logger.debug( 'exectask: newRunner finished %s' % flag.cont )
    return run

class ExecTask( argTask.Task ):
    ''' create an algo/trade runner '''
    
    def __init__(self, orderManager, orderQueue, marketData ):
        super( ExecTask, self ).__init__()        
        self._orderQueue    = orderQueue
        self._marketData    = marketData
        self._orderManager  = orderManager
        self._env           = twkval.getenv( 'run_env' )
        self._flag          = argusutil.Flag( True )
        logger.debug('ExecTask env=%s' % ( self._env ) )
    
    def start(self, tag, logger ):
        logger.debug('ExecTask tag=%s %s' % ( tag, 'start' ) )
        self._flag.cont = True        
        return newRunner( self._orderManager, self._orderQueue, self._marketData, self._flag )
            
    def create(self):
        return self

