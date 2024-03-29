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
    _cx2orig = {}

    def onCreate(self, sessionID):
        logger.debug('onCreate sessionID=%s', sessionID)
        self._sessionID = sessionID
        self._session   = quickfix.Session.lookupSession( sessionID )
        self._cx2orig[ self._sessionID ] = {}

    def setMode(self, mode):
        self._mode = mode

    def getSessionID(self):
        return self._sessionID

    def getSession(self):
        return self._session

    def registerPriceStrip( self, priceStrip ):
        '''setup price strip '''
        self._priceStrip = priceStrip

    def registerStratManager( self, signalStrat ):
        '''callback into the execution sink'''
        self._signalStrat = signalStrat

    def addMessageAdapter( self, msgAdapter ):
        '''callback into the execution sink'''
        self._msgAdapter = msgAdapter

    def onLogon(self, sessionID ):
        logger.debug( 'onLogon: sessionID=%s', sessionID )

    def onLogout(self, sessionID ):
        logger.debug( 'onLogout: sessionID=%s', sessionID )
    
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

        if msgType == fut.Msg_Heartbeat:
            # logger.debug( msgType )
            return

        logger.debug('onToAdmin msgType=%s', fut.msgVal2Name(msgType))
        try:
            if msgType == fut.Msg_Logout or msgType == fut.Msg_Logon:
                logger.debug('onToAdmin msgType=%s message=%s', msgType, message)
                execut.resetSeqNum( sessionID, message, 1 )
        except:
            print 'onFromAdmin ERROR e=%s' % str(traceback.format_exc() )

    def onFromAdmin( self, sessionID, message ):
        hdr     = message.getHeader()
        msgType = hdr.getField( fut.Tag_MsgType )

        if msgType == fut.Msg_Heartbeat:
            # logger.debug( msgType )
            return

        logger.debug('onFromAdmin msgType=%s', fut.msgVal2Name(msgType))

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
        
        mktPrice    = self.getMarketPrices(symbol=symbol)

        self._signalStrat.onFill(
                    signalName  = account,
                    execTime    = txTime,
                    orderId     = orderId,
                    symbol      = symbol,
                    qty         = qty,
                    price       = lastPx,
                    mktPrice    = mktPrice)
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

        if cxqty == 0:
            cxqty  = fut.convertQty( side, int( message.getField( fut.Tag_LeavesQty ) ) )

        try:
            origOrderId = message.getField( fut.Tag_OrigClOrdID )
        except quickfix.FieldNotFound as _e:
            if orderId not in self._cx2orig[ self._sessionID ]:
                logger.error( 'fix.cxed Absent originalId - cx not issued by echo. oid=%s s=%-4s q=%4d' % ( orderId, symbol, cxqty ))
                return
            origOrderId = self._cx2orig[ self._sessionID ][ orderId ]

        mktPrice    = self.getMarketPrices(symbol=symbol)

        logger.debug( 'fix.cxed oid=%s s=%-4s q=%4d' % ( orderId, symbol, cxqty ))
        self._signalStrat.onCxRx(
                    signalName  = account,
                    execTime    = txTime,
                    orderId     = orderId,
                    symbol      = symbol,
                    qty         = cxqty,
                    origOrderId = origOrderId,
                    mktPrice    = mktPrice)

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
                
        mktPrice    = self.getMarketPrices(symbol=symbol)

        self._signalStrat.onCxRx(
                    signalName  = account,
                    execTime    = txTime,
                    orderId     = orderId,
                    symbol      = symbol,
                    qty         = rxqty,
                    origOrderId = None,
                    mktPrice    = mktPrice)

        logger.debug( 'fix.rxed oid=%s s=%-4s q=%4d' % ( orderId, symbol, rxqty ))
    
    def onSubmit( self, orderId, message, execType, orderStatus ):
        logger.debug( 'onSubmit %s %s' % ( execType, orderStatus ) )
        txTime      = message.getField( fut.Tag_TransactTime    )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )
        orderType   = message.getField( fut.Tag_OrderType )
        timeInForce = message.getField( fut.Tag_TimeInForce )

        # cumQty      = int   ( message.getField( fut.Tag_CumQty      ) )
        # leavesQty   = int   ( message.getField( fut.Tag_LeavesQty   ) )

        lastPx      = float ( message.getField( fut.Tag_LastPx      ) )
        lastShares  = int   ( message.getField( fut.Tag_LastShares  ) )
        qty         = fut.convertQty( side, lastShares )

        mktPrice    = self.getMarketPrices(symbol=symbol)

        self._signalStrat.onNew(
            timeInForce = timeInForce,
            signalName  = account,
            execTime    = txTime,
            orderId     = orderId,
            symbol      = symbol,
            orderType   = orderType,
            qty         = qty,
            price       = lastPx,
            mktPrice    = mktPrice)
        logger.debug( 'fix.new formApp onSubmit oid=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, lastPx ))

    def onSubmitToApp( self, orderId, message ):
        logger.debug( 'onSubmitToApp' )
        # orderId     = message.getField( fut.Tag_ClientOrderId   )
        txTime      = message.getField( fut.Tag_TransactTime    )
        side        = message.getField( fut.Tag_Side    )
        symbol      = message.getField( fut.Tag_Symbol  )
        account     = message.getField( fut.Tag_Account )
        orderType   = message.getField( fut.Tag_OrderType )
        timeInForce = message.getField( fut.Tag_TimeInForce )

        price       = 0

        try:
            price      = float ( message.getField( fut.Tag_LastPx      ) )
        except quickfix.FieldNotFound as _e:
            pass

        try:
            price      = float ( message.getField( fut.Tag_Price      ) )
        except quickfix.FieldNotFound as _e:
            pass

        # cumQty      = int   ( message.getField( fut.Tag_CumQty      ) )
        # leavesQty   = int   ( message.getField( fut.Tag_LeavesQty   ) )

        lastShares  = int   ( message.getField( fut.Tag_OrderQty  ) )
        qty         = fut.convertQty( side, lastShares )
        mktPrice    = self.getMarketPrices(symbol=symbol)

        self._signalStrat.onNew(
            signalName  = account,
            execTime    = txTime,
            orderId     = orderId,
            symbol      = symbol,
            qty         = qty,
            price       = price,
            orderType   = orderType,
            timeInForce = timeInForce,
            mktPrice    = mktPrice)

        logger.debug( 'fix.new onSubmitToApp oid=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, price ))

    def onOrderPendingCancel( self, orderId, message, execType, orderStatus ):
        logger.debug( 'onOrderPendingCancel %s %s' % ( execType, orderStatus ) )
        account     = message.getField( fut.Tag_Account )
        symbol      = message.getField( fut.Tag_Symbol  )
        mktPrice    = self.getMarketPrices(symbol=symbol)
        logger.error( 'ERROR!!!!!!!! onOrderPendingCancel: toApp oid=%s s=%-4s' % ( orderId, symbol ))

    def getMarketPrices(self, symbol):
        ''' get Market Prices  '''
        if self._priceStrip is None:
            logger.error( 'ERROR!!!!!!!! getMarketPrices: nor price for %s' % symbol)
            return {}

        trade   = self._priceStrip.getInstantPriceByName(priceType='TRADE', symbol=symbol)
        bid     = self._priceStrip.getInstantPriceByName(priceType='BID', symbol=symbol)
        ask     = self._priceStrip.getInstantPriceByName(priceType='ASK', symbol=symbol)
        return {'TRADE': trade, 'BID': bid, 'ASK': ask}

    ''' order issuing block '''
    def sendOrder( self, senderCompID, targetCompID, account, orderId, symbol, qty, price, timeInForce=fut.Val_TimeInForce_DAY, orderType=None ):
        logger.debug( 'fix.lnk.send account=%s, orderId=%s, symbol=%s, qty=%s, price=%s, timeInForce=%s, orderType=%s',
                      account, orderId, symbol, qty, price, timeInForce, orderType)
        msg = fut.form_NewOrder(
            senderCompID = senderCompID,
            targetCompID = targetCompID,
            account      = account,
            timeInForce  = timeInForce,
            orderId      = orderId,
            symbol       = symbol,
            qty          = qty,
            price        = price,
            orderType    = orderType )
        session = self.getSession()
        session.sendToTarget( msg )
        logger.debug( 'fix.lnk.send  id=%s s=%-4s q=%4d p=%s' % ( orderId, symbol, qty, price ))

    def cancelOrder( self, senderCompID, targetCompID, account, orderId, origOrderId, symbol, qty ):
        logger.debug( 'fix.lnk.cx  enter' )
        msg = fut.form_Cancel(
            senderCompID    = senderCompID,
            targetCompID    = targetCompID,
            account         = account,
            orderId         = orderId,
            origOrderId     = origOrderId,
            symbol          = symbol,
            ccy             = None,
            qty             = qty )

        #self._cx2orig[ orderId ] = origOrderId
        self._cx2orig[ self._sessionID ][ orderId ] = origOrderId

        session = self.getSession()
        session.sendToTarget( msg )
        logger.debug( 'fix.lnk.cx  msg=%s' % ( msg ))
        logger.debug( 'fix.lnk.cx  id=%s s=%-4s q=%4d' % ( orderId, symbol, qty ))

def init(tweakName, signalStrat, mode, pricestrip, cleanSlate=False, msgAdapter=None):
    ''' '''
    cfgpath = execut.initFixConfig( tweakName, cleanSlate=cleanSlate )

    app = Application( )
    app.setMode(mode=mode)
    app.registerStratManager( signalStrat )
    app.addMessageAdapter( msgAdapter )
    app._seenOrderId = set()
    app.registerPriceStrip(pricestrip)

    appThread = execut.AppThread( app=app, cfgpath=cfgpath, useLogger=True )
    appThread.run()
    return appThread, app