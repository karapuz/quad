'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : order.alog module
'''

import heapq
import threading
from   robbie.util.logging import logger

def prettyPrint( instrIx, bidPriceSize, askPriceSize ):
    logger.debug( 'bid: ps=%s,%s ask ps=%s,%s' % ( 
                        bidPriceSize[ 0 ][ instrIx ],bidPriceSize[ 1 ][ instrIx ],
                        askPriceSize[ 0 ][ instrIx ],askPriceSize[ 1 ][ instrIx ], 
                    ) 
                 )
LAST_CANCELALL = 'last_cancellall'

class Base( object ):
    ''' TWAP algo '''

    STATUS_NORMAL = 'normal'
    STATUS_LASTCX = 'last_cancellall'
        
    def __init__(self, relObj, orderExecLink ):
        '''
        relObj        - relation object
        orderExecLink - algo_sendOrder, algo_cancelOrder
        '''
        
        self._relObj        = relObj
        self._orderExecLink = orderExecLink
        
        self._startTime     = None
        self._state         = None
        self._minLot        = 100        
        self._targetWorst   = .02 # no more than two cents away from the price
        self._timeSpent     = 0
        self._cycleLock     = threading.Lock()
        self._levelShift    = .01

    def __repr__(self):
        return '%s,StTm=%s,Stt=%s,TW=%s,TmSpt=%s' % (
                self._name,
                self._startTime,
                self._state,
                self._targetWorst,
                self._timeSpent
            )

    def setTargetWorst(self, t ):
        self._targetWorst   = t # no more than two cents away from the price

    def setLevelShift(self, t ):
        self._levelShift    = t # shift by that many cents when chasing market
                
    def expired(self):
        ''' expired '''
        return self._timeSpent > self._targetTime

    def finish(self):
        ''' expired '''
        raise NotImplemented('algo.finish must be implemented!')

    def nextTime(self, currentTime ):
        ''' nextTime '''
        return max( 0, currentTime - ( self._lastTime +  self._targetStep ) )
        
    def cycle(self, currentTime, bidPriceSize, askPriceSize ):
        with self._cycleLock:
            return self._cycle(currentTime=currentTime, bidPriceSize=bidPriceSize, askPriceSize=askPriceSize )
        
    def _cycle(self, currentTime, bidPriceSize, askPriceSize ):
        self._lastTime  = currentTime
        self._timeSpent = currentTime - self._startTime
        self._timeLeft  = max( 0, self._targetTime - self._timeSpent ) 
        self._stepsLeft = int( self._timeLeft / self._targetStep )        

        if self._state == 'last_cancellall':
            logger.debug( self._state )
            return
        
        elif self._timeSpent > self._targetTime:
            if self._state  == 'normal':
                # logger.debug( 'algo.cycle -> cancellAllPending' )
                self._cancellAllPending( ) # bidPriceSize, askPriceSize
            self._state = 'last_cancellall'

        elif self._state  == 'normal':
            self._issueLimitOrders( bidPriceSize, askPriceSize )
            
        self._refreshHeaps( )

    def targetTime(self):
        ''' '''
        return self._targetTime
    
    def targetStep(self):
        ''' '''
        return self._targetStep

    def _init( self ):
        '''
        initialize exposure
        targetShares     = ( 
            ( 'IBM', ('IBM', 'CASH', 'MS'), 'DRAGON_V1', 1000 ), 
            ( 'MMM', ('MMM', 'CASH', 'MS'), 'BULDOG_V4', 2000 ), ...., )
        
        orders structure
        self._currOrdrs  = ( ( instrIx, expIx, logicalOrderIx, targetShares, physicalOrdersHeap ), ... ( ... ) )
        '''
        
        relObj          = self._relObj
        targetShares    = self._targetShares
        orderExecLink   = self._orderExecLink
        
        newOrdId        = self._orderExecLink.getOrderId

        self._currOrdrs = []
        for instr, expName, stratName, qty in targetShares:
            if not qty:
                continue
            
            logicalOrder = newOrdId(style='L', instr=instr )
            instrIx, expIx, logicalIx = relObj.addTag( instr ), relObj.addTag( expName ), relObj.addTag( logicalOrder )
                        
            orderExecLink.associateStrat( 
                        stratName   = stratName, 
                        instr       = instr, 
                        expName     = expName, 
                        instrIx     = instrIx, 
                        expIx       = expIx, 
                        logicalIx   = logicalIx, qty=qty )
            
            self._currOrdrs.append( ( instrIx, expIx, logicalIx, qty, [] ) ) 

    def start(self, startTime, startState = 'normal' ):
        ''' reset - or start anew for the first time '''
        self._init()
        self._startTime     = startTime
        self._state         = startState

    def status( self ):
        return self._state
    
    def _cancellAllPending( self ):
        rlo = self._relObj
        for instrIx, expIx, logicalIx, _targetShares, orderHeap in self._currOrdrs:
            for _priority, origOrderIx in orderHeap:
                pending = rlo.getPendingByIx( origOrderIx )
                if pending:                
                    self._orderExecLink.algo_cancelOrderLogicalMultiVenue( 
                                            instrIx     = instrIx, 
                                            expIx       = expIx, 
                                            logicalIx   = logicalIx, 
                                            orderShare  = pending, 
                                            origOrderIx = origOrderIx )

    def _refreshHeaps(self):
        ''' removing finished orders from the heap '''
        
        rlo = self._relObj
        currOrders = []
        for instrIx, expIx, logicalIx, targetShares, orderHeap in self._currOrdrs:
            nheap = []
            for priority, orderIx in orderHeap:
                if rlo.getPendingByIx( orderIx ): 
                    heapq.heappush( nheap, ( priority, orderIx ) )
            currOrders.append( ( instrIx, expIx, logicalIx, targetShares, nheap ) )
            
        self._currOrdrs = currOrders

    def _printHeaps(self):
        '''helper method '''
        rlo = self._relObj
        first = False
        for _instrIx, _expIx, _logicalIx, _targetShares, orderHeap in self._currOrdrs:
            for priority, orderIx in orderHeap:
                if rlo.getPendingByIx( orderIx ):
                    if not first:
                        logger.debug( 'V- printheaps' )
                        first = True 
                    logger.debug( 'priority=%6s orderIx=%6s - %6s' % ( priority, orderIx, rlo.getPendingByIx( orderIx ) ) )
        if first:
            logger.debug( 'A-' )

    def _dumpState( self, symbols, shouldPrint=True ):
        ''' dump order state '''
        status = []
        for instr in symbols:
            tag = self._relObj.addTag( instr )
            status.append( { 
                'PEND': self._relObj.getPendingByIx( tag ), 
                'RLZD': self._relObj.getRealizedByIx( tag ), 
                'CNLD': self._relObj.getCanceledByIx( tag ), 
                'RJCT': self._relObj.getRejectedByIx( tag ), 
            })
            if shouldPrint:
                logger.debug( '-> %s' % instr )
                logger.debug( 'PEND %s' % self._relObj.getPendingByIx( tag ) )
                logger.debug( 'RLZD %s' % self._relObj.getRealizedByIx( tag ) ) 
                logger.debug( 'CNLD %s' % self._relObj.getCanceledByIx( tag ) )
                logger.debug( 'RJCT %s' % self._relObj.getRejectedByIx( tag ) )
        return status

    def getRealized( self, symbols ):
        ''' get realized '''
        status = []
        for instr in symbols:
            tag = self._relObj.addTag( instr )
            status.append( self._relObj.getRealizedByIx( tag ) )
        return status
