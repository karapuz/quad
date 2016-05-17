'''
'''
import heapq
import robbie.order.twap_1LR_LGCL as twap

class TWAP( twap.TWAP ):
    ''' TWAP Two Layers algorithm '''
    
    def __init__(self, relObj, orderExecLink, targetShares, targetTime, targetStep ):
        '''
        relObj        - relation object
        targetShares  - tuples ( instrument, amount )
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
        self._name          = 'TWAP_2LR_LGCL'

    def _issueLimitOrders(self, bidPriceSize, askPriceSize ):        
        rlo = self._relObj
        for instrIx, logicalIx, targetShares, orderHeap in self._currOrdrs:
            
            # logger.debug( '_issueLimitOrders: instrIx=%s, logicalIx=%s, targetShares=%s' % ( instrIx, logicalIx, targetShares ) )
            # algo.prettyPrint( instrIx, bidPriceSize, askPriceSize )
            
            if targetShares > 0:
                # buy
                # sell at bid 10, buy at ask 11
                price, size = askPriceSize[ 0 ][ instrIx ], askPriceSize[ 1 ][ instrIx ]
                
                if orderHeap:
                    worstElmnt  = orderHeap[ 0 ]
                    worstPrice, worstOrderIx  = worstElmnt
                    pending     = rlo.getPendingByIx( worstOrderIx )
                    
                    if pending !=0 and worstPrice < price - self._targetWorst:
                        self._orderExecLink.algo_cancelOrderLogical( 
                                                instrIx     = instrIx, 
                                                logicalIx   = logicalIx, 
                                                orderShare  = pending, 
                                                origOrderIx = worstOrderIx )
                    
                availableShares = targetShares - ( rlo.getPendingByIx( logicalIx ) + rlo.getRealizedByIx( logicalIx ) ) 
                shareSign       = 1
                price1          = price
                price2          = price - 0.01
                
                priority1       = price1
                priority2       = price2

            elif targetShares <= 0:
                # sell
                # sell at bid 10, buy at ask 11
                price, size = bidPriceSize[ 0 ][ instrIx ], bidPriceSize[ 1 ][ instrIx ]
                
                if orderHeap:
                    worstElmnt  = orderHeap[ 0 ]
                    worstPrice, worstOrderIx  = worstElmnt
                    worstPrice  = -worstPrice
                    pending     = rlo.getPendingByIx( worstOrderIx )
                    
                    if pending !=0 and worstPrice > price + self._targetWorst:
                        self._orderExecLink.algo_cancelOrderLogical( 
                                                instrIx     = instrIx, 
                                                logicalIx   = logicalIx, 
                                                orderShare  = pending, 
                                                origOrderIx = worstOrderIx )

                availableShares = -( targetShares - ( rlo.getPendingByIx( logicalIx ) + rlo.getRealizedByIx( logicalIx ) ) )
                shareSign       = -1
                price1          =  price
                price2          =  price + 0.01                
                priority1       = -price1
                priority2       = -price2
                            
            if availableShares > 0:
                if self._stepsLeft:
                    orderShare1 = max( self._minLot, min( size, availableShares / ( self._stepsLeft ) ) )
                    orderShare2 = max( self._minLot, min( size, ( availableShares - orderShare1 ) / ( self._stepsLeft ) ) )
                else:
                    orderShare1 = max( self._minLot, size )
                    orderShare2 = orderShare1
                    
                orderIx = self._orderExecLink.algo_sendOrderLogical( 
                                            instrIx     = instrIx, 
                                            logicalIx   = logicalIx, 
                                            orderShare  = int( shareSign*orderShare1 ), 
                                            price       = price1 )
                
                heapq.heappush( orderHeap, ( priority1, orderIx ) )
                
                orderIx = self._orderExecLink.algo_sendOrderLogical( 
                                            instrIx     = instrIx, 
                                            logicalIx   = logicalIx, 
                                            orderShare  = int( shareSign*orderShare2 ), 
                                            price       = price2 )
                
                heapq.heappush( orderHeap, ( priority2, orderIx ) )
