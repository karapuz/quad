'''
'''
import meadow.order.twap_2LR_LGCL as twap

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
        self._name          = 'TWAP_2LR_INSTR'

    def _init(self):                
        # sorted current orders by price
        # logicalIx for this order is the whole instrument
        relObj = self._relObj
        targetShares = self._targetShares
        instrIxs = [ ( relObj.addTag( instr ), shares ) for instr, shares in targetShares ]
        self._currOrdrs = [ [ instrIx, instrIx, shares, [] ] for instrIx, shares in instrIxs ]

