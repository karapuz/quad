'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : execution.adapter module
'''

import os
import datetime
import threading
import robbie.fix.util as fut
import robbie.tweak.value as twkval
from   robbie.util.logging import logger, ThreadedLoggerExecution, LoggerExecution


class SignalStratManager( object ):
    '''
    relObj     - used to record fills, cancels, rejects.
    linkObj    - order stream consumer/execution stream producer.
    linkObj.registerStratManager
               - defines the listener (consumer) for the execution stream. It is 'self' here
                 the listener should have onFill, onCancel, onReject methods defined
    
    '''
    def __init__(self, signalStratObj, relObj, linkObj, initialExposure, execTimeFunc=None ):
        self._orderIdPrefix             = datetime.datetime.now().strftime( '%Y%m%d%H%M' )    
        self._orderId                   = 0
        self._orderId2ix                = {}
        self._cxOrigOrderId2ordeId      = {}
        self._stratLogicalOrderIx       = {}
        self._sso                       = signalStratObj

        self._execTime      = execTimeFunc if execTimeFunc else datetime.datetime.now
        self._relObj        = relObj
        self._linkObj       = linkObj

        # if we start with a portfolio
        self._iExp          = initialExposure
        self._orderIdLock   = threading.Lock()
        self._linkObj.registerStratManager( self )

        logginMode          = 'f'
        if twkval.getenv( 'run_env' )  == 'unittest':
            self._ldn   = LoggerExecution( dn=os.path.join( logger.dirName(), 'execution' ), mode=logginMode, name = 'trade'  )
            self._lgcldn= LoggerExecution( dn=os.path.join( logger.dirName(), 'execution' ), mode=logginMode, name = 'logical' )
        else:
            self._ldn   = ThreadedLoggerExecution( dn=os.path.join( logger.dirName(), 'execution' ), mode=logginMode, name = 'trade' )
            self._lgcldn= ThreadedLoggerExecution( dn=os.path.join( logger.dirName(), 'execution' ), mode=logginMode, name = 'logical' )

    def execTime(self):
        return self._execTime()

    def getInitExp(self):
        ''' accessor method '''
        return self._iExp

    def getRelObj(self):
        ''' accessor method '''
        return self._relObj

    def strExecTime(self):
        return self._execTime.strftime( '%d/%m/%Y  %H:%M:%S.f' )
        
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
    