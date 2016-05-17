'''
'''
import heapq
import robbie.order.algo as orderalgo
import robbie.order.twap_1LR_LGCL as twap
from   robbie.util.logging import logger

class TWAP( twap.TWAP ):
    ''' TWAP Two Layers algorithm 
        Using multi venue manager api
    '''
    
    def __init__(self, relObj, orderExecLink, targetShares, targetTime, targetStep ):
        '''
        relObj        - relation object
        targetShares  - tuples ( instrument, expName, stratName, amount )
        targetTime    - in seconds (1s, 2s, 5s etc )
        targetStep    - in seconds (.1s, .2s, etc )
        orderExecLink - algo_sendOrder, algo_cancelOrder
        '''
        
        super( TWAP, self ).__init__( relObj, orderExecLink, targetShares, targetTime, targetStep )
        
        self._startTime     = None
        self._state         = None
        self._minLot        = 100
        
        self._targetShares  = targetShares
        self._targetTime    = targetTime
        self._targetStep    = targetStep
        self._targetWorst   = .02 # no more than two cents away from the price
        self._name          = 'TWAP_2LR_LGCL_MV'
        self._levelShift    = .01

    def _issueLimitOrders(self, bidPriceSize, askPriceSize ):        
        rlo = self._relObj
        priceArrIx, _cumSizeIx, sizeArrIx   = 0, 1, 2

        for instrIx, expIx, logicalIx, targetShares, orderHeap in self._currOrdrs:

            if targetShares > 0:
                # buy
                # sell at bid 10, buy at ask 11                
                price, size = askPriceSize[ priceArrIx ][ instrIx ], askPriceSize[ sizeArrIx ][ instrIx ]
                if orderHeap:
                    worstElmnt  = orderHeap.pop( 0 )
                    worstPrice, worstOrderIx  = worstElmnt
                    pending     = rlo.getPendingByIx( worstOrderIx )
                    
                    if pending !=0:
                        if worstPrice < price - self._targetWorst:
                            self._orderExecLink.algo_cancelOrderLogicalMultiVenue( 
                                                    instrIx     = instrIx,
                                                    expIx       = expIx,
                                                    logicalIx   = logicalIx, 
                                                    orderShare  = pending, 
                                                    origOrderIx = worstOrderIx )
                        else:
                            heapq.heappush( orderHeap, ( worstPrice, worstOrderIx ) )

                availableShares = targetShares - ( rlo.getPendingByIx( logicalIx ) \
                                                 + rlo.getRealizedByIx( logicalIx ) ) 
                shareSign       = 1
                price1          = price
                price2          = price1 - self._levelShift
                price3          = price2 - self._levelShift
                
                priority1       = price1
                priority2       = price2
                priority3       = price2

            elif targetShares <= 0:
                # sell
                # sell at bid 10, buy at ask 11
                price, size = bidPriceSize[ priceArrIx ][ instrIx ], bidPriceSize[ sizeArrIx ][ instrIx ]
                
                if orderHeap:
                    worstElmnt  = orderHeap.pop( 0 )
                    worstPrice, worstOrderIx  = worstElmnt
                    worstPrice  = -worstPrice
                    pending     = rlo.getPendingByIx( worstOrderIx )
                    
                    if pending !=0:
                        if worstPrice > price + self._targetWorst:
                            self._orderExecLink.algo_cancelOrderLogicalMultiVenue( 
                                                    instrIx     = instrIx, 
                                                    expIx       = expIx,
                                                    logicalIx   = logicalIx, 
                                                    orderShare  = pending, 
                                                    origOrderIx = worstOrderIx )
                        else:
                            heapq.heappush( orderHeap, ( worstPrice, worstOrderIx ) )

                availableShares = -( targetShares - ( rlo.getPendingByIx( logicalIx ) 
                                                    + rlo.getRealizedByIx( logicalIx ) ) )
                shareSign       = -1
                price1          =  price
                price2          =  price1 + self._levelShift
                price3          =  price2 + self._levelShift
                priority1       = -price1
                priority2       = -price2
                priority3       = -price3
                            
            if availableShares > 0:
                topSize = int( size / 2 )
                
                if self._stepsLeft:
                    orderShare1 = min( topSize,  availableShares, max( topSize, int( availableShares / self._stepsLeft ) ) )
                    availableShares1 = availableShares - orderShare1
                    availableShares2 = availableShares1 - orderShare1
                    orderShare2 = min( topSize,  availableShares1, max( topSize, int( availableShares1 / self._stepsLeft ) ) )
                    orderShare3 = min( topSize,  availableShares2, max( topSize, int( availableShares2 / self._stepsLeft ) ) )
                else:
                    orderShare1 = min( topSize, availableShares )
                    orderShare2 = min( topSize, ( availableShares - orderShare1 ) )
                    orderShare3 = min( topSize, ( availableShares - ( orderShare1 - orderShare2 ) ) )
                
                orderShare1  = int( shareSign * orderShare1 )
                
                orderIx = self._orderExecLink.algo_sendOrderLogicalMultiVenue( 
                                            instrIx     = instrIx,
                                            expIx       = expIx,
                                            logicalIx   = logicalIx,
                                            orderShare  = orderShare1,
                                            price       = price1 )
                
                heapq.heappush( orderHeap, ( priority1, orderIx ) )
                
                if orderShare2:     
                    orderShare2 = int( shareSign*orderShare2 )
                    
                    orderIx = self._orderExecLink.algo_sendOrderLogicalMultiVenue( 
                                                instrIx     = instrIx, 
                                                expIx       = expIx,
                                                logicalIx   = logicalIx, 
                                                orderShare  = orderShare2,
                                                price       = price2 )
                
                    heapq.heappush( orderHeap, ( priority2, orderIx ) )

                if orderShare3:     
                    orderShare3 = int( shareSign*orderShare3 )
                    
                    orderIx = self._orderExecLink.algo_sendOrderLogicalMultiVenue( 
                                                instrIx     = instrIx, 
                                                expIx       = expIx,
                                                logicalIx   = logicalIx, 
                                                orderShare  = orderShare3,
                                                price       = price3 )
                
                    heapq.heappush( orderHeap, ( priority3, orderIx ) )

    def finish(self):
        try:
            # with self._cycleLock:
            self._finish()
        except:
            import traceback
            logger.error( 'algo.finish -> FAILED' )
            logger.error( traceback.format_exc() )
            
    def _finish(self):
        ''' expired '''
        logger.debug( 'algo.finish state=%s' % str( self._state ) )
        
        if self._state != orderalgo.LAST_CANCELALL:
            self._cancellAllPending()
            logger.error( 'algo.finish -> still cancelling' )
        else:
            logger.debug( 'algo.finish -> canceled already' )
            