import numpy

import meadow.fix.util as fut
from   meadow.lib.logging import logger

class ExecLink( object ):
    def __init__( self, startTime, instrMap  ):
        self._liveOrders= []
        self._cxOrders  = []
        self._time      = startTime
        self._instrMap  = instrMap
        self._filled    = []
        self._spread    = []

    def _onFill( self, execTime, orderId, symbol, qty, price ):
        self._filled.append( ( execTime, orderId, symbol, qty, price ) )

    def registerExecSink( self, manager ):
        self._manager = manager
             
    def cancelOrder( self, orderId, origOrderId, symbol, qty, tagVal=None ):
        
        liveOrders = []
        for ( oid, instr, share, price ) in self._liveOrders:
            if oid == origOrderId:            
                self._cxOrders.append( ( oid, symbol, qty ) )                
                share -= qty
            if share:
                liveOrders.append( ( oid, instr, share, price ) )
                
        self._liveOrders = liveOrders

    def sendOrder( self, orderId, symbol, qty, price, timeInForce=fut.Val_TimeInForce_DAY, tagVal=None ):        
        self._liveOrders.append( ( orderId, symbol, qty, price ) )

    def marketMoves(self, bidPriceSize, askPriceSize ):
        liveOrders = []
        priceArrIx, _cumSizeIx, sizeArrIx   = 0, 1, 2
        
        for ( orderId, symbol, orderShare, limitPrice ) in self._liveOrders:
            self._time += 1
            instrIx     = self._instrMap[ symbol ]
            share       = 0
        
            if orderShare > 0:

                price, size = askPriceSize[ priceArrIx ][ instrIx ], askPriceSize[ sizeArrIx ][ instrIx ]
                if price < .01:
                    # logger.debug( 'skipping %s' % str( ( price, size ) ) )
                    continue

                if limitPrice >= price:
#                    print '+'
                    share = int( min( orderShare, size ) )
                    self._manager.onFill( 
                            execTime    = self._time, 
                            orderId     = orderId, 
                            symbol      = symbol, 
                            qty         = share, 
                            price       = price )

                    self._onFill(
                            execTime    = self._time, 
                            orderId     = orderId, 
                            symbol      = symbol, 
                            qty         = share, 
                            price       = price )

            elif orderShare <= 0:
                price, size = bidPriceSize[ priceArrIx ][ instrIx ], bidPriceSize[ sizeArrIx ][ instrIx ]
                if price < .01:
                    # logger.debug( 'skipping %s' % str( ( price, size ) ) )
                    continue
                
                if limitPrice <= price:
                    share   = min( -orderShare, size )
                    share   = int( -share )
                    
                    self._manager.onFill( 
                            execTime    = self._time, 
                            orderId     = orderId, 
                            symbol      = symbol, 
                            qty         = share, 
                            price       = price )

                    self._onFill(
                            execTime    = self._time, 
                            orderId     = orderId, 
                            symbol      = symbol, 
                            qty         = share, 
                            price       = price )
                    
            leftOver = orderShare - share 
            if leftOver:
                liveOrders.append( ( orderId, symbol, leftOver, limitPrice ) )
        
        self._liveOrders = liveOrders

        for ( orderId, symbol, share ) in self._cxOrders:
            self._time += 1
            self._manager.onCancel( 
                    execTime    = self._time, 
                    orderId     = orderId, 
                    symbol      = symbol, 
                    qty         = share )
                
        self._cxOrders = []

            
    def analyse(self):
        if not self._filled:
            # logger.debug( 'Nothing to analyse')
            return
        #        tix = 0
        #        qix = 3
        #        pix = 4
        ps  = []
        pqs = []
        qs  = 0
        for ( _execTime, _orderId, _symbol, qty, price ) in self._filled:
            ps.append( price )
            pqs.append( qty * price )
            qs += qty

        mu      = numpy.sum( pqs ) / qs
        sigma   = numpy.std( ps )

        spread  = numpy.array( self._spread )
        prices  = .5* ( spread[:,0] + spread[:,1] )
        mu1     = numpy.mean( prices )
        dm1     = numpy.mean( spread[:,0] - spread[:,1] )
        ds1     = numpy.std( spread[:,0] - spread[:,1] )
        firstPrice = numpy.mean( spread[0] )
        
        # logger.debug( 'p0=%s mu=%s mu1=%s s=%s dm1=%s ds1=%s' % ( firstPrice, mu, mu1, sigma, dm1, ds1 ) )
        return firstPrice, mu, mu1, sigma, dm1, ds1
