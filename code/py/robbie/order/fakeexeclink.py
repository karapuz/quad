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
     
    def algo_sendOrder( self, instrIx, orderShare, price ):
        orderId = self.getOrderId(style='L', instr=instrIx)
        orderIx = self._relObj.addTag( orderId )        
        
        logger.debug( 'SEND orderIx=%6s instrIx=%6s orderShare=%6s price=%6s' % ( orderIx, instrIx, orderShare, price ) )
        
        self._relObj.addPendingByIx( [instrIx, orderIx], [orderShare, orderShare], verbose=False )
        
        logicalIx=instrIx
        
        iExp = self._iExp[ instrIx ] + self._relObj.getRealizedByIx( instrIx )
        _bsdir, _octype, qty, _tagVal = ordman.computeBSDirOCType( iExp, orderShare )
        
        self._liveOrders.append( ( orderIx, logicalIx, instrIx, qty, price ) )
        return orderIx

    def algo_sendOrderLogical( self, instrIx, logicalIx, orderShare, price ):
        orderId = self.getOrderId(style='L', instr=instrIx)
        orderIx = self._relObj.addTag( orderId )        
        
        logger.debug( 'SEND_LOGICAL orderIx=%6s logicalIx=%6s instrIx=%6s orderShare=%6s price=%6s' % ( orderIx, instrIx, logicalIx, orderShare, price ) )
        
        self._relObj.addPendingByIx( [instrIx, logicalIx, orderIx], [orderShare, orderShare, orderShare], verbose=False )

        iExp = self._iExp[ instrIx ] + self._relObj.getRealizedByIx( instrIx )
        _bsdir, _octype, qty, _tagVal = ordman.computeBSDirOCType( iExp, orderShare )
        
        self._liveOrders.append( ( orderIx, logicalIx, instrIx, qty, price ) )
        return orderIx

    def algo_cancelOrder( self, instrIx, orderShare, origOrderIx ):
        
        orderShare = int( orderShare )
        logger.debug( 'CNCL origOrderIx=%6s instrIx=%6s orderShare=%6s' % ( origOrderIx, instrIx, orderShare  ) )
        
        self._relObj.addCanceledByIx( [ instrIx, origOrderIx ], [orderShare, orderShare], verbose=False )

        logicalIx=instrIx        
        self._liveOrders.append( ( origOrderIx, logicalIx, instrIx, orderShare, None ) )
        return instrIx

    def algo_cancelOrderLogical( self, instrIx, logicalIx, orderShare, origOrderIx ):
        
        orderShare = int( orderShare )
        logger.debug( 'CNCL_LOGICAL origOrderIx=%6s instrIx=%6s logicalIx=%6s orderShare=%6s' % ( origOrderIx, instrIx, logicalIx, orderShare  ) )
        
        self._relObj.addCanceledByIx( [ instrIx, logicalIx, origOrderIx ], [ orderShare, orderShare, orderShare ], verbose=False )
        
        self._liveOrders.append( ( origOrderIx, logicalIx, instrIx, orderShare, None ) )
        return instrIx

    def marketMoves(self, bidPriceSize, askPriceSize ):
        liveOrders = []
        for ( orderIx, logicalIx, instrIx, orderShare, limitPrice ) in self._liveOrders:
            share = 0
            if orderShare > 0:
                price, size = askPriceSize[0][ instrIx ], askPriceSize[0][ instrIx ]
                if limitPrice >= price:
                    share = int( min( orderShare, size ) )
                    self._relObj.addRealizedByIx( [ instrIx, logicalIx, orderIx ], [ share, share, share ] )
                    logger.debug( 'F B  orderIx=%6s logicalIx=%6s instrIx=%6s orderShare=%6s price=%6s @%s' % ( orderIx, logicalIx, instrIx, orderShare, price, price ) )
                    
            elif orderShare <= 0:
                price, size = bidPriceSize[0][ instrIx ], bidPriceSize[0][ instrIx ]
                if limitPrice <= price:
                    share = min( -orderShare, size )
                    share = int( -share )
                    self._relObj.addRealizedByIx( [ instrIx, logicalIx, orderIx ], [ share, share, share ] )
                    logger.debug( 'F S  orderIx=%6s logicalIx=%6s instrIx=%6s orderShare=%6s price=%6s @%s' % ( orderIx, logicalIx, instrIx, orderShare, price, price ) )
                    
            if share - orderShare:
                liveOrders.append( ( orderIx, logicalIx, instrIx, orderShare-share, price ) )
        
        self._liveOrders = liveOrders
        