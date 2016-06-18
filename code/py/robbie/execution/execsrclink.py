'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : execution.execsrclink - fixlink for the exec source
'''

import datetime
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
        # logger.debug('onCreate self._session=%s', self._session)

    def getSessionID(self):
        return self._sessionID

    def getSession(self):
        return self._session
    
    def onLogon(self, sessionID ):
        # logger.debug('onLogon')
        pass

    def onLogout(self, sessionID ):
        # logger.debug('onLogout')
        pass
    
    def toAdmin(self, message, sessionID ): 
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.Tag_MsgType )
        logger.debug('toAdmin msgType=%s', msgType)
    
    def fromAdmin(self, message, sessionID ):
        try:
            return self.onFromAdmin( sessionID, message )
        except:
            logger.error('fromAdmin ERROR')
            logger.error( traceback.format_exc() )
        
    def toApp(self, message, sessionID ): 
        try:
            if self._msgAdapter:
                with self._msgAdapter(message, 'fromApp'):
                    return self.onToApp( sessionID, message )
            else:
                return self.onToApp( sessionID, message )
        except:
            logger.error( '---------------> %s', traceback.format_exc() )
    
    def fromApp(self, message, sessionID):
        try:
            if self._msgAdapter:
                with self._msgAdapter(message, 'fromApp'):
                    return self.onFromApp( sessionID, message )
            else:
                return self.onFromApp( sessionID, message )
        except:
            logger.error( '---------------> %s', traceback.format_exc() )

    def registerStratManager( self, signalStrat ):
        '''callback into the execution sink'''
        self._signalStrat = signalStrat

    def addMessageAdapter( self, msgAdapter ):
        '''callback into the execution sink'''
        self._msgAdapter = msgAdapter

    '''
    onEvent handlers
    '''
    def onFromAdmin( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.Tag_MsgType )

        logger.debug('onFromAdmin msgType=%s', msgType)

        if msgType == fut.Msg_Heartbeat:
            logger.debug( msgType )
            return

        try:
            if msgType == fut.Msg_Logout or msgType == fut.Msg_Logon:
                execut.resetSeqNum( sessionID, message )
        except:
            print '--------------> e=%s' % str(traceback.format_exc() )

    def onFromApp( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.name2tag('MsgType') )

        logger.debug('onFromApp msgType=%s', msgType)
    
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
                logger.error( 'onFromApp [1] unhandled %s %s %s' % ( msgType, execType, orderStatus ) )
        else:
            logger.error( 'onFromApp [2] unhandled %s %s %s' % ( msgType, execType, orderStatus ) )

    def onToApp( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.name2tag('MsgType') )

        logger.debug('onToApp msgType=%s', msgType)

        if msgType == fut.Msg_NewOrderSingle:
            # execType    = message.getField( fut.Tag_ExecType    )
            # orderStatus = message.getField( fut.Tag_OrderStatus )

             return self.onSubmitToApp( message )
        else:
            logger.error( 'onToApp [1] unhandled %s %s %s' % ( msgType, execType, orderStatus ) )

    def onOrderFill( self, message, execType, orderStatus ):
        ''' '''
        logger.debug( 'onOrderFill %s %s' % ( execType, orderStatus ) )
        
        orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )
        # txTime      = datetime.datetime.now()

        lastPx      = float ( message.getField( fut.Tag_LastPx      ) )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )

        # cumQty      = int   ( message.getField( fut.Tag_CumQty      ) )
        # leavesQty   = int   ( message.getField( fut.Tag_LeavesQty   ) )

        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        qty         = fut.convertQty( side, lastShares )
        
        self._signalStrat.onFill( signalName=account, execTime=txTime, orderId=orderId, symbol=symbol, qty=qty, price=lastPx )
        logger.debug( 'fix.fill oid=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, lastPx ))

    def onOrderCancel( self, message, execType, orderStatus ):
        ''' '''
        logger.debug( 'onOrderCancel %s %s' % ( execType, orderStatus ) )
        orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )
        
        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )

        if lastShares == 0:
            cumQty  = fut.convertQty( side, int( message.getField( fut.Tag_CumQty ) ) )
            orderQty= fut.convertQty( side, int( message.getField( fut.Tag_OrderQty ) ) )        
            cxqty   = orderQty - cumQty
        else:
            cxqty   = fut.convertQty( side, lastShares )
              
        logger.debug( 'fix.cxed oid=%s s=%-4s q=%4d' % ( orderId, symbol, cxqty ))
        self._signalStrat.onCxRx( signalName=account, execTime=txTime, orderId=orderId, symbol=symbol, qty=cxqty )

    def onOrderReject( self, message, execType, orderStatus ):
        ''' '''
        logger.debug( 'onOrderReject %s %s' % ( execType, orderStatus ) )
        orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )

        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )

        if lastShares == 0:
            cumQty  = fut.convertQty( side, int( message.getField( fut.Tag_CumQty ) ) )
            orderQty= fut.convertQty( side, int( message.getField( fut.Tag_OrderQty ) ) )        
            rxqty   = orderQty - cumQty
        else:
            rxqty   = fut.convertQty( side, lastShares )
                
        self._signalStrat.onCxRx(signalName=account, execTime=txTime, orderId=orderId, symbol=symbol, qty=rxqty )
        logger.debug( 'fix.rxed oid=%s s=%-4s q=%4d' % ( orderId, symbol, rxqty ))
    
    def onSubmit( self, message, execType, orderStatus ):
        # logger.debug( 'onSubmit %s %s' % ( execType, orderStatus ) )
        logger.debug( 'onSubmit %s %s' % ( execType, orderStatus ) )
        orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )

        # cumQty      = int   ( message.getField( fut.Tag_CumQty      ) )
        # leavesQty   = int   ( message.getField( fut.Tag_LeavesQty   ) )

        lastPx      = float ( message.getField( fut.Tag_LastPx      ) )
        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        qty         = fut.convertQty( side, lastShares )

        self._signalStrat.onNew( signalName=account, execTime=txTime, orderId=orderId, symbol=symbol, qty=qty, price=lastPx )
        logger.debug( 'fix.new oid=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, lastPx ))

    def onSubmitToApp( self, message ):
        logger.debug( 'onSubmitToApp' )
        orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )

        # cumQty      = int   ( message.getField( fut.Tag_CumQty      ) )
        # leavesQty   = int   ( message.getField( fut.Tag_LeavesQty   ) )

        #lastPx      = float ( message.getField( fut.Tag_LastPx      ) )
        lastShares  = int   ( message.getField( fut.Tag_OrderQty  ) )
        qty         = fut.convertQty( side, lastShares )
        lastPx      = 0

        self._signalStrat.onNew( signalName=account, execTime=txTime, orderId=orderId, symbol=symbol, qty=qty, price=lastPx )
        logger.debug( 'fix.new oid=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, lastPx ))

    def onOrderPendingCancel( self, message, execType, orderStatus ):
        logger.debug( 'onOrderPendingCancel %s %s' % ( execType, orderStatus ) )
        account     = message.getField( fut.Tag_Account )

    ''' order issuing block '''
    def sendOrder( self, senderCompID, targetCompID, account, orderId, symbol, qty, price, timeInForce=fut.Val_TimeInForce_DAY, tagVal=None ):
        # senderCompID = 'BANZAI',
        # targetCompID = 'FIXIMULATOR',
        # logger.debug( 'fix.new  enter' )
        msg = fut.form_NewOrder(
            senderCompID = senderCompID,
            targetCompID = targetCompID,
            account      = account,
            timeInForce  = timeInForce,
            orderId      = orderId,
            symbol       = symbol,
            qty          = qty,
            price        = price,
            tagVal       = tagVal )

        session = self.getSession()
        session.sendToTarget( msg )
        logger.debug( 'fix.new  id=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, price ))

    def cancelOrder( self, orderId, origOrderId, symbol, qty, tagVal=None ):
        msg = 'fix.cx  id=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty)
        logger.error( msg )
        raise ValueError(msg)
        
def init(signalStrat, msgAdapter=None):
    ''' '''
    cfgpath     = execut.initFixConfig( 'fix_SrcConnConfig' )

    app         = Application( )
    app.registerStratManager( signalStrat )
    app.addMessageAdapter( msgAdapter )

    appThread   = execut.AppThread( app=app, cfgpath=cfgpath )
    appThread.run()
    return appThread, app