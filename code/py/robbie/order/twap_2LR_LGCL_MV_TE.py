'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : order.twap_2LR_LGCL_MV_TE module
'''

import heapq
import robbie.order.algo as orderalgo
from   robbie.util.logging import logger
import robbie.order.twap_1LR_LGCL as twap

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
        self._name          = 'TWAP_2LR_LGCL_MV_TE'
        self._levelShift    = .01
        self._maxQueue      = 3
        self._minRemove     = 1
        self._skipSpikes    = False
        self._maxSpike      = .01

    def setMaxQueue(self, l ):
        self._maxQueue = l

    def setMinRemove(self, l ):
        self._minRemove = l

    def setSkipSpikes( self, l ):
        self._skipSpikes = l
        
    def setMaxSpike( self, l ):
        self._maxSpike = l

    def _issueLimitOrders(self, bidPriceSize, askPriceSize, debug=False ):
        rlo = self._relObj
        priceArrIx, _cumSizeIx, sizeArrIx   = 0, 1, 2

        # debug=True
        
        for instrIx, expIx, logicalIx, targetShares, orderHeap in self._currOrdrs:

            askPrice, askSize = askPriceSize[ priceArrIx ][ instrIx ], askPriceSize[ sizeArrIx ][ instrIx ]
            bidPrice, bidSize = bidPriceSize[ priceArrIx ][ instrIx ], bidPriceSize[ sizeArrIx ][ instrIx ]

            if debug:
                logger.debug( '_issueLimitOrders: %s ask=%s bid=%s' % (
                    str( ( instrIx, expIx, logicalIx, targetShares ) ),
                    str( ( askPrice, askSize ) ), 
                    str( ( bidPrice, bidSize ) ), 
                    ) 
                )
            
            basisPoints = ( askPrice - bidPrice )/( .5 * ( askPrice + bidPrice )  )
            if basisPoints > self._maxSpike:
                if self._skipSpikes:
                    logger.debug( 'skipping %f > %f' % ( basisPoints, self._maxSpike ) )
                    continue
            if orderHeap:
                N = max( self._minRemove, len( orderHeap ) - self._maxQueue )
                # print N, self._minRemove, len( orderHeap ), self._maxQueue
                for _Ni in range( N ):        
                    _worstPrice, worstOrderIx = heapq.heappop( orderHeap )
                    pending = rlo.getPendingByIx( worstOrderIx )                    
                    if pending != 0:
                        self._orderExecLink.algo_cancelOrderLogicalMultiVenue( 
                                                instrIx     = instrIx,
                                                expIx       = expIx,
                                                logicalIx   = logicalIx, 
                                                orderShare  = pending, 
                                                origOrderIx = worstOrderIx )

            if targetShares > 0:
                # buy
                # sell at bid 10, buy at ask 11                
                # price, size = askPriceSize[ priceArrIx ][ instrIx ], askPriceSize[ sizeArrIx ][ instrIx ]
                price, size     = askPrice, askSize

                availableShares = targetShares - ( rlo.getPendingByIx( logicalIx ) \
                                                 + rlo.getRealizedByIx( logicalIx ) ) 
                shareSign       = 1
                price1          = price
                price2          = price - self._levelShift
                
                priority1       = price1
                priority2       = price2

            elif targetShares < 0:
                # sell
                # sell at bid 10, buy at ask 11
                # price, size = bidPriceSize[ priceArrIx ][ instrIx ], bidPriceSize[ sizeArrIx ][ instrIx ]
                price, size     = bidPrice, bidSize
                
                availableShares = -( targetShares - ( rlo.getPendingByIx( logicalIx )
                                                    + rlo.getRealizedByIx( logicalIx ) ) )
                shareSign       = -1
                price1          =  price
                price2          =  price + self._levelShift
                
                priority1       = -price1
                priority2       = -price2
            else:
                logger.error( '_issueLimitOrders: skipping %s: targetShares=%f' % ( instrIx, str( targetShares ) ) )                
                            
            if availableShares > 0:
                topSize = int( size / 2 )
                
                if self._stepsLeft:
                    orderShare1 = min( topSize,  availableShares, max( topSize, int( availableShares / self._stepsLeft ) ) )
                    res1        = availableShares - orderShare1
                    orderShare2 = min( topSize,  res1, max( topSize, int( res1/ self._stepsLeft ) ) )
                else:
                    orderShare1 = min( topSize, availableShares )
                    orderShare2 = min( topSize, ( availableShares - orderShare1 ) )
                
                orderShare1  = int( shareSign*orderShare1 )
                
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
            