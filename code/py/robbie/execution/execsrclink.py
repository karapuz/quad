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
from   robbie.echo.stratutil import EXECUTION_MODE

class Application( quickfix.Application ):

    def onCreate(self, sessionID):
        logger.debug('onCreate sessionID=%s', sessionID)
        self._sessionID = sessionID
        self._session   = quickfix.Session.lookupSession( sessionID )

    def setMode(self, mode):
        self._mode = mode

    def getSessionID(self):
        return self._sessionID

    def getSession(self):
        return self._session
    
    def registerStratManager( self, signalStrat ):
        '''callback into the execution sink'''
        self._signalStrat = signalStrat

    def addMessageAdapter( self, msgAdapter ):
        '''callback into the execution sink'''
        self._msgAdapter = msgAdapter

    def onLogon(self, sessionID ):
        # logger.debug('onLogon')
        pass

    def onLogout(self, sessionID ):
        # logger.debug('onLogout')
        pass
    
    def toAdmin(self, message, sessionID ): 
        try:
            if self._msgAdapter:
                with self._msgAdapter(message, 'fromApp'):
                    return self.onToAdmin( sessionID, message )
            else:
                return self.onToAdmin( sessionID, message )
        except:
            logger.error( 'toAdmin: ERROR %s', traceback.format_exc() )

    def fromAdmin(self, message, sessionID ):
        try:
            if self._msgAdapter:
                with self._msgAdapter(message, 'fromApp'):
                    return self.onFromAdmin( sessionID, message )
            else:
                 return self.onFromAdmin( sessionID, message )
        except:
            logger.error( 'fromAdmin: ERROR %s', traceback.format_exc() )
        
    def toApp(self, message, sessionID ): 
        try:
            if self._mode == EXECUTION_MODE.NEW_FILL_CX:
                onToApp = self.onToApp
            elif self._mode == EXECUTION_MODE.FILL_ONLY:
                onToApp = self.onToAppFillOnly
            else:
                raise ValueError('Unknown mode=%s' % self._mode)

            if self._msgAdapter:
                with self._msgAdapter(message, 'fromApp'):
                    onToApp( sessionID, message )
            else:
                return onToApp( sessionID, message )
        except:
            logger.error( 'toApp: ERROR %s', traceback.format_exc() )
    
    def fromApp(self, message, sessionID):
        try:
            if self._msgAdapter:
                with self._msgAdapter(message, 'fromApp'):
                    return self.onFromApp( sessionID, message )
            else:
                return self.onFromApp( sessionID, message )
        except:
            logger.error( 'fromApp: ERROR %s', traceback.format_exc() )

    ''' onEvent handlers '''

    def onToAdmin( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.Tag_MsgType )
        logger.debug('onToAdmin msgType=%s', fut.msgVal2Name(msgType))

    def onFromAdmin( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.Tag_MsgType )
        logger.debug('onFromAdmin msgType=%s', fut.msgVal2Name(msgType))

        if msgType == fut.Msg_Heartbeat:
            logger.debug( msgType )
            return

        try:
            if msgType == fut.Msg_Logout or msgType == fut.Msg_Logon:
                execut.resetSeqNum( sessionID, message )
        except:
            print 'onFromAdmin ERROR e=%s' % str(traceback.format_exc() )

    def onFromApp( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.Tag_MsgType )

        logger.debug('onFromApp msgType=%s', fut.msgVal2Name(msgType))

        if msgType == fut.Msg_ExecReport:
            execType    = message.getField( fut.Tag_ExecType    )
            orderStatus = message.getField( fut.Tag_OrderStatus )
            orderId     = message.getField( fut.Tag_ClientOrderId   )

            if execType == fut.Val_ExecType_New:

                if orderId in self._seenOrderId:
                    logger.error('onFromApp: see duplicate orderId=%s', orderId)
                    return
                self._seenOrderId.add( orderId )

                return self.onSubmit( orderId=orderId, message=message, execType=execType, orderStatus=orderStatus )

            elif orderStatus in ( fut.Val_OrderStatus_Fs ):
                return self.onOrderFill( orderId=orderId, message=message, execType=execType, orderStatus=orderStatus )

            elif orderStatus == fut.Val_OrderStatus_Cx:
                return self.onOrderCancel( orderId=orderId, message=message, execType=execType, orderStatus=orderStatus )

            elif orderStatus == fut.Val_OrderStatus_Rx:
                return self.onOrderReject( orderId=orderId, message=message, execType=execType, orderStatus=orderStatus )
            
            elif orderStatus == fut.Val_OrderStatus_Pnd_Cx:
                return self.onOrderPendingCancel( orderId=orderId, message=message, execType=execType, orderStatus=orderStatus )
            
            else:
                logger.error( 'onFromApp [1] unhandled %s %s %s' % ( msgType, execType, orderStatus ) )
        else:
            logger.error( 'onFromApp [2] unhandled %s' % ( msgType ) )

    def onToAppFillOnly( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.name2tag('MsgType') )
        logger.debug('onToAppFillOnly msgType=%s', fut.msgVal2Name(msgType))

    def onToApp( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.name2tag('MsgType') )
        logger.debug('onToApp msgType=%s', fut.msgVal2Name(msgType))

        orderId = message.getField( fut.Tag_ClientOrderId )

        if orderId in self._seenOrderId:
            logger.error('onToApp: see duplicate orderId=%s', orderId)
            return
        self._seenOrderId.add( orderId )

        if msgType == fut.Msg_NewOrderSingle:
             return self.onSubmitToApp( orderId=orderId, message=message )

        # elif msgType == fut.Msg_OrderCancelRequest:
        #      return  self.onOrderCancelToApp( orderId=orderId, message=message)

        else:
            logger.error( 'onToApp [1] unhandled %s' % ( msgType  ) )

    def onOrderFill( self, orderId, message, execType, orderStatus ):
        ''' '''
        logger.debug( 'onOrderFill %s %s' % ( execType, orderStatus ) )
        
        txTime      = message.getField( fut.Tag_TransactTime    )

        lastPx      = float ( message.getField( fut.Tag_LastPx      ) )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )
        # orderType   = message.getField( fut.Tag_OrderType )

        # cumQty      = int   ( message.getField( fut.Tag_CumQty      ) )
        # leavesQty   = int   ( message.getField( fut.Tag_LeavesQty   ) )

        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        qty         = fut.convertQty( side, lastShares )
        
        self._signalStrat.onFill( signalName=account, execTime=txTime, orderId=orderId, symbol=symbol, qty=qty, price=lastPx )
        logger.debug( 'fix.fill oid=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, lastPx ))

    def onOrderCancelToApp( self, orderId, message):
        return self.onOrderCancel( orderId=orderId, message=message, execType=None, orderStatus=None )

    def onOrderCancel( self, orderId, message, execType, orderStatus ):
        ''' '''
        # logger.debug( 'onOrderCancel %s %s' % ( execType, orderStatus ) )
        logger.debug( 'onOrderCancel %s' % str(message) )

        # orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )
        
        lastShares  = int( message.getField( fut.Tag_LastShares  ))
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )
        # orderType   = message.getField( fut.Tag_OrderType )
        side        = message.getField( fut.Tag_Side    )

        if lastShares == 0:
            cumQty  = fut.convertQty( side, int( message.getField( fut.Tag_CumQty ) ) )
            orderQty= fut.convertQty( side, int( message.getField( fut.Tag_OrderQty ) ) )        
            cxqty   = orderQty - cumQty
        else:
            cxqty   = fut.convertQty( side, lastShares )

        origOrderId = message.getField( fut.Tag_OrigClOrdID )

        logger.debug( 'fix.cxed oid=%s s=%-4s q=%4d' % ( orderId, symbol, cxqty ))
        self._signalStrat.onCxRx( signalName=account, execTime=txTime, orderId=orderId, symbol=symbol, qty=cxqty, origOrderId=origOrderId )

    def onOrderReject( self, orderId, message, execType, orderStatus ):
        ''' '''
        logger.debug( 'onOrderReject %s %s' % ( execType, orderStatus ) )
        # orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )

        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )
        # orderType   = message.getField( fut.Tag_OrderType )

        if lastShares == 0:
            cumQty  = fut.convertQty( side, int( message.getField( fut.Tag_CumQty ) ) )
            orderQty= fut.convertQty( side, int( message.getField( fut.Tag_OrderQty ) ) )        
            rxqty   = orderQty - cumQty
        else:
            rxqty   = fut.convertQty( side, lastShares )
                
        self._signalStrat.onCxRx(signalName=account, execTime=txTime, orderId=orderId, symbol=symbol, qty=rxqty, origOrderId=None )
        logger.debug( 'fix.rxed oid=%s s=%-4s q=%4d' % ( orderId, symbol, rxqty ))
    
    def onSubmit( self, orderId, message, execType, orderStatus ):
        # logger.debug( 'onSubmit %s %s' % ( execType, orderStatus ) )
        logger.debug( 'onSubmit %s %s' % ( execType, orderStatus ) )
        # orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )

        # cumQty      = int   ( message.getField( fut.Tag_CumQty      ) )
        # leavesQty   = int   ( message.getField( fut.Tag_LeavesQty   ) )

        lastPx      = float ( message.getField( fut.Tag_LastPx      ) )
        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        qty         = fut.convertQty( side, lastShares )

        self._signalStrat.onNew(
            signalName  = account,
            execTime    = txTime,
            orderId     = orderId,
            symbol      = symbol,
            qty         = qty,
            price       = lastPx )
        logger.debug( 'fix.new formApp oid=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, lastPx ))

    def onSubmitToApp( self, orderId, message ):
        logger.debug( 'onSubmitToApp' )
        # orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )
        orderType   = message.getField( fut.Tag_OrderType )

        # cumQty      = int   ( message.getField( fut.Tag_CumQty      ) )
        # leavesQty   = int   ( message.getField( fut.Tag_LeavesQty   ) )

        #lastPx      = float ( message.getField( fut.Tag_LastPx      ) )
        lastShares  = int   ( message.getField( fut.Tag_OrderQty  ) )
        qty         = fut.convertQty( side, lastShares )
        lastPx      = 0

        self._signalStrat.onNew(
            signalName  = account,
            execTime    = txTime,
            orderId     = orderId,
            symbol      = symbol,
            qty         = qty,
            price       = lastPx,
            orderType   = orderType)

        logger.debug( 'fix.new toApp oid=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, lastPx ))

    def onOrderPendingCancel( self, orderId, message, execType, orderStatus ):
        logger.debug( 'onOrderPendingCancel %s %s' % ( execType, orderStatus ) )
        account     = message.getField( fut.Tag_Account )

    ''' order issuing block '''
    def sendOrder( self, senderCompID, targetCompID, account, orderId, symbol, qty, price, timeInForce=fut.Val_TimeInForce_DAY, tagVal=None ):
        logger.debug( 'fix.lnk.send  enter')
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
        logger.debug( 'fix.lnk.send  id=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, price ))

    def cancelOrder( self, senderCompID, targetCompID, account, orderId, origOrderId, symbol, qty ):
        logger.debug( 'fix.lnk.cx  enter' )
        msg = fut.form_Cancel(
            senderCompID    = senderCompID,
            targetCompID    = targetCompID,
            account         = account,
            orderId         = orderId,
            origOrderId     = origOrderId,
            symbol          = symbol,
            qty             = qty )
        session = self.getSession()
        session.sendToTarget( msg )
        logger.debug( 'fix.lnk.cx  msg=%s' % ( msg ))
        logger.debug( 'fix.lnk.cx  id=%s s=%-4s q=%4d' % ( orderId, symbol, qty ))

def init(tweakName, signalStrat, mode, msgAdapter=None):
    ''' '''
    cfgpath     = execut.initFixConfig( tweakName )

    app         = Application( )
    app.setMode(mode=mode)
    app.registerStratManager( signalStrat )
    app.addMessageAdapter( msgAdapter )
    app._seenOrderId = set()

    appThread   = execut.AppThread( app=app, cfgpath=cfgpath )
    appThread.run()
    return appThread, app