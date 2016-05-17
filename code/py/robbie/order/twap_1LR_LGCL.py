'''
'''

import heapq
import robbie.order.algo as algo

class TWAP( algo.Base ):
    ''' TWAP algo '''
    
    def __init__(self, relObj, orderExecLink, targetShares, targetTime, targetStep ):
        '''
        relObj        - relation object
        targetShares  - tuples ( instrument, amount )
        targetTime    - in seconds (1s, 2s, 5s etc )
        targetStep    - in seconds (.1s, .2s, etc )
        orderExecLink - algo_sendOrder, algo_cancelOrder
        '''
        
        super( TWAP, self ).__init__( relObj, orderExecLink )
        
        self._startTime     = None
        self._state         = None
        self._minLot        = 100
        
        self._targetShares  = targetShares
        self._targetTime    = targetTime
        self._targetStep    = targetStep
        self._targetWorst   = .02 # no more than two cents away from the price
        self._name          = 'TWAP_1LR_LGCL'

    def __repr__(self):
        return '%s,StTm=%s,Stt=%s,TW=%s,TmSpt=%s,TrgtT=%s,TrgtS=%s' % (
                self._name,
                self._startTime,
                self._state,
                self._targetWorst,
                self._timeSpent,
                self._targetTime,
                self._targetStep,
            )
                
    def _issueLimitOrders(self, bidPriceSize, askPriceSize ):        
        rlo = self._relObj
        
        for instrIx, logicalIx, targetShares, orderHeap in self._currOrdrs:
            if targetShares > 0:
                # buy
                # sell at bid 10, buy at ask 11
                price, size = askPriceSize[ 0 ][ instrIx ], askPriceSize[ 1 ][ instrIx ]
                
                if orderHeap:
                    worstElmnt  = orderHeap[ 0 ]
                    worstPrice, worstOrderIx  = worstElmnt
                    pending     = rlo.getPendingByIx( worstOrderIx )
                    
                    if pending != 0 and worstPrice < price - self._targetWorst:
                        self._orderExecLink.algo_cancelOrderLogical( instrIx=instrIx, logicalIx=logicalIx, orderShare=pending, origOrderIx=worstOrderIx )
                    
                priority        = price
                availableShares = targetShares - ( rlo.getPendingByIx( logicalIx ) + rlo.getRealizedByIx( logicalIx ) ) 
                shareSign       = 1 

            elif targetShares <= 0:
                # sell
                # sell at bid 10, buy at ask 11
                price, size = bidPriceSize[ 0 ][ instrIx ], bidPriceSize[ 1 ][ instrIx ]
                
                if orderHeap:
                    worstElmnt  = orderHeap[ 0 ]
                    worstPrice, worstOrderIx  = worstElmnt
                    worstPrice  = -worstPrice
                    pending     = rlo.getPendingByIx( worstOrderIx )
                    
                    if pending != 0 and worstPrice > price + self._targetWorst:
                        self._orderExecLink.algo_cancelOrderLogical( instrIx=instrIx, logicalIx=logicalIx, orderShare=pending, origOrderIx=worstOrderIx )

                priority        = -price
                availableShares = -( targetShares - ( rlo.getPendingByIx( logicalIx ) + rlo.getRealizedByIx( logicalIx ) ) )
                shareSign       = -1 
                            
            if availableShares > 0:
                if self._stepsLeft:
                    orderShare = max( self._minLot, min( size, availableShares / ( self._stepsLeft ) ) )
                else:
                    orderShare = max( self._minLot, size )
                    
                orderIx = self._orderExecLink.algo_sendOrderLogical( 
                                    instrIx=instrIx, 
                                    logicalIx=logicalIx, 
                                    orderShare=int( shareSign*orderShare ), 
                                    price=price )
                heapq.heappush( orderHeap, ( priority, orderIx ) )
