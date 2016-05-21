'''
'''

import os
import datetime
import threading
import robbie.fix.util as fut
import robbie.tweak.value as twkval
# import robbie.allocation.util as alut
# import robbie.allocation.shortlocates as shortlocates
from   robbie.util.logging import logger, ThreadedLoggerExecution, LoggerExecution

'''
The value of tag 77 will indicate whether the swap position is being increased or closed out.

TagID    Value    Description
77       O        Open
77       C        Close

Tag 54 will indicate the side of the swap request:

TagID    Value    Description
54       1        Buy
54       2        Sell
54       5        Sell short

'''

class OrderManager( object ):
    '''
    relObj     - used to record fills, cancels, rejects.

    linkObj    - order stream consumer/execution stream producer.

    linkObj.registerExecSink
               - defines the listener (consumer) for the execution stream. It is 'self' here
                 the listener should have onFill, onCancel, onReject methods defined
    
    '''
    def __init__(self, relObj, linkObj, initialExposure, execTimeFunc=None ):
        self._orderIdPrefix             = datetime.datetime.now().strftime( '%Y%m%d%H%M' )    
        self._orderId                   = 0
        self._orderId2ix                = {}
        self._cxOrigOrderId2ordeId      = {}
        self._stratLogicalOrderIx       = {}
        
        self._relObj        = relObj
        self._linkObj       = linkObj

        # if we start with a portfolio
        self._iExp          = initialExposure
        
        self._execTime      = execTimeFunc if execTimeFunc else datetime.datetime.now
                
        self._linkObj.registerExecSink( self )
        
        self._orderIdLock   = threading.Lock()
        
        logginMode          = 'f'
        if twkval.getenv( 'run_env' )  == 'unittest':
            self._ldn   = LoggerExecution( dn=os.path.join( logger.dirName(), 'execution' ), mode=logginMode, name = 'trade'  )
            self._lgcldn= LoggerExecution( dn=os.path.join( logger.dirName(), 'execution' ), mode=logginMode, name = 'logical' )
        else:
            self._ldn   = ThreadedLoggerExecution( dn=os.path.join( logger.dirName(), 'execution' ), mode=logginMode, name = 'trade' )
            self._lgcldn= ThreadedLoggerExecution( dn=os.path.join( logger.dirName(), 'execution' ), mode=logginMode, name = 'logical' )

    def strExecTime(self):
        return self._execTime.strftime( '%d/%m/%Y  %H:%M:%S.f' )
        
    def associateStrat( self, stratName, instr, expName,  instrIx, expIx, logicalIx, qty ):
        ''' associate this logical order (for a specific instrument) with this strategy '''
        
        if stratName not in self._stratLogicalOrderIx:
            self._stratLogicalOrderIx[ stratName ] = []

        venue = alut.allocParts( allocName=expName, partNames=('venue', 'type' ), sep='-' )
        
        self._lgcldn.trade( execType=stratName, execTime=self.execTime(), orderId=venue, symbol=instr, qty=qty, price=instrIx, logicalIx=logicalIx )            
        self._stratLogicalOrderIx[ stratName ].append( ( instrIx, expIx, logicalIx ) )

    def expByStrat(self, stratName, productType, typ='realized' ):
        ''' extract exposure for these logical order (for a specific instrument) for this strategy '''
        expByGroup = { typ: {}, 'full': {} }
        
        if stratName not in self._stratLogicalOrderIx:
            logger.debug( 'expByStrat: %s has no logical requests yet.' % stratName )
            return expByGroup
        
        if productType == 'ALL':
            groupBy = 'instr'
            
        elif productType in ( 'CASH', 'SWAP' ):
            groupBy = 'exposure'
        else:
            raise ValueError( 'Unknown productType=%s' % productType )
        
        # pendingByInstr  = {}
        for ( instrIx, expIx, logicalIx ) in self._stratLogicalOrderIx[ stratName ]:
            expName = self._relObj.getTagByIx( expIx )
            if groupBy == 'instr':
                groupName   = self._relObj.getTagByIx( instrIx )
                
            elif groupBy == 'exposure':
                groupName, prodType = alut.allocParts( allocName=expName, partNames=( 'symbol', 'type' ), sep=None )
                if prodType != productType:
                    logger.debug( 'mgr.expByStrat: Skipping %s' % str( prodType ) )
                    continue
            else:
                raise ValueError( 'Unknown groupBy=%s' % groupBy )
            
            if groupName not in expByGroup[ typ ]:
                expByGroup[ typ ][ groupName ] = 0
            
            if expName not in expByGroup[ 'full' ]:
                expByGroup[ 'full' ][ expName ] = 0
            
            if typ == 'realized':
                addExp = self._relObj.getRealizedByIx( logicalIx )
                expByGroup[ typ    ][ groupName ] += addExp
                expByGroup[ 'full' ][ expName   ] += addExp
            else:
                raise ValueError( 'Unknown type=%s' % typ )
            
        return expByGroup

    def execTime(self):
        return self._execTime()
    
    def getInitExp(self):
        ''' accessor method '''
        return self._iExp
    
    def getRelObj(self):
        ''' accessor method '''
        return self._relObj
    
    def getOrderId( self, style, instr ):
        with self._orderIdLock:
            self._orderId += 1
            return '%s%s%s' % ( self._orderIdPrefix, style, self._orderId )

    def isCancelled( self, origOrderId ):
        return origOrderId in self._cxOrigOrderId2ordeId
    
    def markCancelled( self, origOrderId, orderId ):
        self._cxOrigOrderId2ordeId[ origOrderId ] = orderId
        
    def setOrderId2ix(self, orderId, ix ):
        self._orderId2ix[ orderId ] = ix

    def getOrderId2ix(self, orderId ):
        return self._orderId2ix[ orderId ]

    def reportExpNicely(self, exp0, exp1, qty, nqty):
        excl = 'iExp!' if qty != nqty else ''
        logger.debug( 'mgr.**   exp=%s qty=%s %s' % ( str( ( exp0, exp1 ) ), str( ( qty, nqty ) ), excl ), neverPrint=True )

    def stratAssoc(self, execType, symbol, expName, qty, logicalIx, price ):
        ''' record logical association with a strategy '''
        execTime = self.execTime()
        self._lgcldn.trade(execType=execType, execTime=execTime, orderId=expName, symbol=symbol, qty=qty, price=price, logicalIx=logicalIx )                

    def cancelOrder(self, orderId, origOrderId, instr, expName, qty ):
        ''' simple cancel '''
        
        ixs = self._relObj.addTags( ( instr, expName, origOrderId, origOrderId ) )        
        self.setOrderId2ix( orderId, ixs )

        _instrIx, expIx, _orderIx, _logicalId = ixs
        orderType = 'N'
        tagVal  = instrSpecificTags( orderType=orderType, expName=expName )

        logger.debug( 'mgr.cx   oid=%s eix=%-5d qty=%4d' % ( orderId, expIx, qty ), neverPrint=True )
        
        execTime = self.execTime()
        
        self._ldn.trade(execType='SC', execTime=execTime, orderId=orderId, symbol=instr, qty=qty, price=origOrderId, logicalIx=None )
        self._linkObj.cancelOrder( orderId=orderId, origOrderId=origOrderId, symbol=instr, qty=qty, tagVal=tagVal )

    def sendOrder(self, orderId, instr, expName, qty, price, timeInForce=fut.Val_TimeInForce_DAY ):
        ''' simple send new'''

        ixs = self._relObj.addTags( ( instr, expName, orderId, orderId ) )        
        self.setOrderId2ix( orderId, ixs )
        
        _instrIx, expIx, orderIx, _logicalId = ixs
        
        exp0, exp1  = self._iExp[ expIx ], self._relObj.getRealizedByIx( expIx )                
        # _bsdir, _octype, nqty, tagVal = computeBSDirOCType( exp0 + exp1, qty )
        
        # orderType='N'
        # tagVal  = instrSpecificTags( orderType=orderType, expName=expName, tagVal=tagVal )

        self.reportExpNicely( exp0=exp0, exp1=exp1, qty=qty, nqty=nqty )

        tagVal = None
        nqty = qty
        qtys = ( nqty, ) * len( ixs )
        self._relObj.addPendingByIx( ixs, qtys, verbose=False )
        logger.debug( 'mgr.new  oid=%s eix=%-5d qty=%4d nqty=%d price=%f' % ( orderIx, expIx, qty, nqty, price ), neverPrint=True )
        
        execTime = self.execTime()
        
        self._ldn.trade(execType='SN', execTime=execTime, orderId=orderId, symbol=instr, qty=nqty, price=price, logicalIx=None )                
        self._linkObj.sendOrder( orderId=orderId, symbol=instr, qty=nqty, price=price, timeInForce=timeInForce, tagVal=tagVal )

    def onFill(self, execTime, orderId, symbol, qty, price ):
        '''
        1. check if the order originates here. If not, ignore
        2. retrieve the index of affected blocks. ( 2 for instrument level, 3 for instrmunet+logical order level )
        3. update realized values for the blocks from [2]
        '''
        if orderId not in self._orderId2ix:
            logger.info( 'mgr.fld  oid=%s did not originate' % orderId, neverPrint=True )
            self._ldn.trade(execType='FU', execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price, logicalIx=None)
            return
        
        logger.debug( 'mgr.fld  oid=%s s=%-4s q=%4d' % ( orderId, symbol, qty ), neverPrint=True  )
        
        ( instrIx, expIx, logicalIx, origOrderIx ) = self._orderId2ix[ orderId ]
        
        self._ldn.trade(execType='F', execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price, logicalIx=logicalIx )
        
        ixs     = ( instrIx, expIx, logicalIx, origOrderIx )
        qtys    = ( qty, ) * len( ixs )
        
        self._relObj.addRealizedByIx( ixs, qtys )

    def onCancel(self, execTime, orderId, symbol, qty ):
        '''
        1. check if the referenced order originates here. If not, ignore
        2. retrieve the index of affected blocks. ( 2 for instrument level, 3 for instrmunet+logical order level )
        3. update cancelled values for the blocks from [2]
        '''
        
        if orderId not in self._orderId2ix:
            logger.info( 'mgr.cxed oid=%s did not originate' % orderId )
            self._ldn.trade(execType='CU', execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=None, logicalIx=None )
            return

        logger.debug( 'mgr.cxed oid=%s s=%-4s q=%4d' % ( orderId, symbol, qty ), neverPrint=True )        
        ( instrIx, expIx, logicalIx, origOrderIx ) = self._orderId2ix[ orderId ]
        
        self._ldn.trade(execType='C', execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=origOrderIx, logicalIx=logicalIx )
        
        ixs     = ( instrIx, expIx, logicalIx, origOrderIx )
        qtys    = ( qty, ) * len( ixs )
        
        self._relObj.addCanceledByIx( ixs, qtys )

    def onReject(self, execTime, orderId, symbol, qty ):
        '''
        1. check if the referenced order originates here. If not, ignore
        2. retrieve the index of affected blocks. ( 2 for instrument level, 3 for instrmunet+logical order level )
        3. update rejected values for the blocks from [2]
        '''
        
        if orderId not in self._orderId2ix:
            self._ldn.trade(execType='RU', execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=None, logicalIx=None )
            logger.info( 'mgr.rxed oid=%s did not originate' % orderId, neverPrint=True )
            return

        logger.debug( 'mgr.rxed oid=%s s=%s q=%s' % ( orderId, symbol, qty ), neverPrint=True )

        ( instrIx, expIx, logicalIx, origOrderIx ) = self._orderId2ix[ orderId ]
        
        self._ldn.trade(execType='R', execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=origOrderIx, logicalIx=logicalIx )
        
        ixs     = ( instrIx, expIx, logicalIx, origOrderIx )
        qtys    = ( qty, ) * len( ixs )
        
        self._relObj.addRejectedByIx( ixs, qtys )
    