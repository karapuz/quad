from   robbie.lib.logging import logger
import robbie.order.manager as ordman

class ExecLink( object ):
    def __init__(self, relObj, initialExposure ):
        self._id        = 0
        self._relObj    = relObj
        self._iExp      = initialExposure
        self._liveOrders= []
        
    def getOrderId(self, style, instr ):
        i = self._id
        self._id += 1
        return '%s_%s_%s' % ( style, instr, i )
     
    def algo_sendOrderLogicalMultiVenue( self, instrIx, expIx, logicalIx, orderShare, price ):
        orderId = self.getOrderId('L', instr=instrIx )
        orderIx = self._relObj.addTag( orderId )        
        
        logger.debug( 'new oid=%6s loid=%6s iix=%6s eix=%6s qty=%6s p=%6s' % 
                      ( orderIx, instrIx, expIx, logicalIx, orderShare, price ) )
        ixs = ( instrIx, expIx, logicalIx, orderIx )
        self._relObj.addPendingByIx( ixs, ( orderShare, ) * len( ixs ), verbose=False )

        iExp = self._iExp[ expIx ] + self._relObj.getRealizedByIx( expIx )
        _bsdir, _octype, qty, _tagVal = ordman.computeBSDirOCType( iExp, orderShare )
        
        self._liveOrders.append( ( orderIx, logicalIx, instrIx, expIx, qty, price ) )
        return orderIx

    def algo_cancelOrderLogicalMultiVenue( self, instrIx, expIx, logicalIx, orderShare, origOrderIx ):
        
        orderShare = int( orderShare )
        logger.debug( 'CNCL_LOGICAL origOrderIx=%6s instrIx=%6s logicalIx=%6s orderShare=%6s' % ( origOrderIx, instrIx, logicalIx, orderShare  ) )
        
        ixs = ( instrIx, expIx, logicalIx, origOrderIx  )
        self._relObj.addCanceledByIx( ixs, ( orderShare, ) * len( ixs ), verbose=False )
        
        self._liveOrders.append( ( origOrderIx, logicalIx, instrIx, expIx, orderShare, None ) )
        return instrIx

    def marketMoves(self, bidPriceSize, askPriceSize ):
        liveOrders = []
        for ( orderIx, logicalIx, instrIx, expIx, orderShare, limitPrice ) in self._liveOrders:
            share = 0
            if orderShare > 0:
                price, size = askPriceSize[0][ instrIx ], askPriceSize[0][ instrIx ]
                if limitPrice >= price:
                    share = int( min( orderShare, size ) )
                    ixs = ( instrIx, expIx, logicalIx, orderIx )
                    self._relObj.addRealizedByIx( ixs, ( share, ) * len( ixs ) )
                    logger.debug( 'F B  orderIx=%6s logicalIx=%6s instrIx=%6s orderShare=%6s price=%6s @%s' % 
                        ( orderIx, logicalIx, instrIx, orderShare, price, price ) )
                    
            elif orderShare <= 0:
                price, size = bidPriceSize[0][ instrIx ], bidPriceSize[0][ instrIx ]
                if limitPrice <= price:
                    share = min( -orderShare, size )
                    share = int( -share )
                    ixs = ( instrIx, expIx, logicalIx, orderIx )
                    self._relObj.addRealizedByIx( ixs, ( share, ) * len( ixs ) )
                    logger.debug( 'F S  orderIx=%6s logicalIx=%6s instrIx=%6s orderShare=%6s price=%6s @%s' % 
                        ( orderIx, logicalIx, instrIx, orderShare, price, price ) )
                    
            if share - orderShare:
                liveOrders.append( ( orderIx, logicalIx, instrIx, expIx, orderShare-share, price ) )
        
        self._liveOrders = liveOrders
        