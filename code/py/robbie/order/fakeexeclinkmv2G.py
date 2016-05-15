import meadow.fix.util as fut
from   meadow.lib.logging import logger

class ExecLink( object ):
    def __init__( self, startTime, instrMap  ):
        self._liveOrders= []
        self._cxOrders  = []
        self._time      = startTime
        self._instrMap  = instrMap

    def registerExecSink( self, manager ):
        self._manager = manager
             
    def cancelOrder( self, orderId, origOrderId, symbol, qty, tagVal=None ):
        # print 'cancelOrder( %s )' % str( ( orderId, origOrderId, symbol, qty ) )
        
        liveOrders = []
        for ( oid, instr, share, price ) in self._liveOrders:
            if oid == origOrderId:            
                self._cxOrders.append( ( oid, symbol, qty ) )                
                share -= qty
            if share:
                liveOrders.append( ( oid, instr, share, price ) )
                
        self._liveOrders = liveOrders

    def sendOrder( self, orderId, symbol, qty, price, timeInForce=fut.Val_TimeInForce_DAY, tagVal=None ):        
        # print 'sendOrder( %s )' % str( ( orderId, symbol, qty, price ) )
        self._liveOrders.append( ( orderId, symbol, qty, price ) )

    def marketMoves(self, bidPriceSize, askPriceSize ):
        liveOrders = []
        
        for ( orderId, symbol, orderShare, limitPrice ) in self._liveOrders:
            # print 'marketMoves %s' % str( ( orderId, symbol, orderShare, limitPrice ) )
            self._time += 1
            instrIx     = self._instrMap[ symbol ]
            share       = 0
            
            if orderShare > 0:
                price, size = askPriceSize[0][ instrIx ], askPriceSize[1][ instrIx ]
                if limitPrice >= price:
                    share = int( min( orderShare, size ) )
                    self._manager.onFill( 
                            execTime    = self._time, 
                            orderId     = orderId, 
                            symbol      = symbol, 
                            qty         = share, 
                            price       = price )
                    
            elif orderShare <= 0:
                price, size = bidPriceSize[0][ instrIx ], bidPriceSize[1][ instrIx ]
                if limitPrice <= price:
                    share   = min( -orderShare, size )
                    share   = int( -share )
                    
                    self._manager.onFill( 
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
