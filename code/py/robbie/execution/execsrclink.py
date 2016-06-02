'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : execution.execsrclink - fixlink for the exec source
'''

import traceback

import quickfix as quickfix
import robbie.fix.util as fut
import robbie.execution.util as execut
from   robbie.util.logging import logger

class Application( quickfix.Application ):

    def onCreate(self, sessionID):
        logger.debug('onCreate sessionID=%s', sessionID)
        self._sessionID = sessionID
        self._session   = quickfix.Session.lookupSession( sessionID )
    
    def getSessionID(self):
        return self._sessionID

    def getSession(self):
        return self._session
    
    def onLogon(self, sessionID ):
        #libreport.reportInfo(subject='FIX LOGIN', txt='Argus has logged in' )
        logger.debug('onLogon')

    def onLogout(self, sessionID ):
        #libreport.reportError(subject='FIX LOGOUT', txt='Argus has logged out' )
        logger.debug('onLogout')
    
    def toAdmin(self, message, sessionID ): 
        logger.debug('toAdmin')
    
    def fromAdmin(self, message, sessionID ):
        try:
            return self.onFromAdmin( sessionID, message )
        except:
            logger.debug('fromAdmin')
            logger.error( traceback.format_exc() )
        
    def toApp(self, message, sessionID ): 
        # logger.debug('toApp')
        pass
    
    def fromApp(self, message, sessionID):
        try:
            return self.onFromApp( sessionID, message )
        except:
            logger.error( traceback.format_exc() )

    def registerExecSink( self, sink ):
        '''callback into the execution sink'''
        self._execSink = sink

    '''
    onEvent handlers
    '''
    def onFromAdmin( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.Tag_MsgType )
    
        if msgType == fut.Msg_Heartbeat:
            logger.debug( msgType )
            return
        
        if msgType == fut.Msg_Logout or msgType == fut.Msg_Logon:
            execut.resetSeqNum( sessionID, message )

    def onFromApp( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.name2tag('MsgType') )
    
        if msgType == fut.Msg_ExecReport:
            execType    = message.getField( fut.Tag_ExecType    )
            orderStatus = message.getField( fut.Tag_OrderStatus )
            
            if execType == fut.Val_ExecType_New:
                return self.onSubmit( message, execType, orderStatus )

            elif orderStatus in ( fut.Val_OrderStatus_Fs ):
                return self.onOrderFill( message, execType, orderStatus )

            elif orderStatus == fut.Val_OrderStatus_Cx:
                return self.onOrderCancel( message, execType, orderStatus )

            elif orderStatus == fut.Val_OrderStatus_Rx:
                return self.onOrderReject( message, execType, orderStatus )
            
            elif orderStatus == fut.Val_OrderStatus_Pnd_Cx:
                return self.onOrderPendingCancel( message, execType, orderStatus )
            
            else:
                logger.error( 'onFromApp unhandled %s %s %s' % ( msgType, execType, orderStatus ) )
            
    def onOrderFill( self, message, execType, orderStatus ):
        # logger.debug( 'onOrderFill %s %s' % ( execType, orderStatus ) )
        
        orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )
        
        lastPx      = float ( message.getField( fut.Tag_LastPx      ) )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        
        # cumQty      = int   ( message.getField( fut.Tag_CumQty      ) )
        # leavesQty   = int   ( message.getField( fut.Tag_LeavesQty   ) )

        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        qty         = fut.convertQty( side, lastShares )
        
        self._execSink.onFill( execTime=txTime, orderId=orderId, symbol=symbol, qty=qty, price=lastPx ) 
        logger.debug( 'fix.fill oid=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, lastPx ), neverPrint=True )

    def onOrderCancel( self, message, execType, orderStatus ):
        orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )
        
        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        
        if lastShares == 0:
            cumQty  = fut.convertQty( side, int( message.getField( fut.Tag_CumQty ) ) )
            orderQty= fut.convertQty( side, int( message.getField( fut.Tag_OrderQty ) ) )        
            cxqty   = orderQty - cumQty
        else:
            cxqty   = fut.convertQty( side, lastShares )
              
        logger.debug( 'fix.cxed oid=%s s=%-4s q=%4d' % ( orderId, symbol, cxqty ), neverPrint=True )
        self._execSink.onCancel( execTime=txTime, orderId=orderId, symbol=symbol, qty=cxqty )         

    def onOrderReject( self, message, execType, orderStatus ):
        orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )

        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        
        if lastShares == 0:
            cumQty  = fut.convertQty( side, int( message.getField( fut.Tag_CumQty ) ) )
            orderQty= fut.convertQty( side, int( message.getField( fut.Tag_OrderQty ) ) )        
            rxqty   = orderQty - cumQty
        else:
            rxqty   = fut.convertQty( side, lastShares )
                
        self._execSink.onReject(execTime=txTime, orderId=orderId, symbol=symbol, qty=rxqty )
        logger.debug( 'fix.rxed oid=%s s=%-4s q=%4d' % ( orderId, symbol, rxqty ), neverPrint=True )
    
    def onSubmit( self, message, execType, orderStatus ):
        # logger.debug( 'onSubmit %s %s' % ( execType, orderStatus ) )
        pass

    def onOrderPendingCancel( self, message, execType, orderStatus ):
        # logger.debug( 'onOrderPendingCancel %s %s' % ( execType, orderStatus ) )
        pass

    ''' order issuing block '''
    def sendOrder( self, orderId, symbol, qty, price, timeInForce=fut.Val_TimeInForce_DAY, tagVal=None ):
        msg = 'fix.new  id=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, price )
        logger.error( msg, neverPrint=True )
        raise ValueError(msg)

    def cancelOrder( self, orderId, origOrderId, symbol, qty, tagVal=None ):
        msg = 'fix.cx  id=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty)
        logger.error( msg, neverPrint=True )
        raise ValueError(msg)
        
def init():
    '''
    with twcx.Tweaks(
        fix_root=os.path.join( logger.dirName(), 'fix' ),
        fix_connConfig={ 'host': 9999, 'port': '10.1.1.230', 'sender': 'CLIENT1', 'target': 'IREACH' } ):
    '''

    cfgpath     = execut.initFixConfig( 'fix_SrcConnConfig' )
    app         = Application( )
    appThread   = execut.AppThread( app=app, cfgpath=cfgpath )
    appThread.run()
    return appThread, None
