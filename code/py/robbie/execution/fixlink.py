'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : execution.fixlink module
'''

import traceback
import threading

import quickfix as quickfix
import robbie.fix.util as fut
import robbie.tweak.value as twval
import robbie.fix.config as fixccfg
import robbie.lib.report as libreport
import robbie.fix.seqnum as seqnumutil
from   robbie.util.logging import logger

import robbie.lib.environment as environment

def resetSeqNum( sessionID, message ):
    try:
        return _resetSeqNum( sessionID, message )
    except quickfix.FieldNotFound as _e:
        # logger.debug( 'Caught FieldNotFound=%s' % str(e) )
        logger.debug( 'Caught FieldNotFound')
         
def _resetSeqNum( sessionID, message ):
    text = message.getField( fut.Tag_Text )
        
    p = text.split(' ') # 'Logon seqnum 60 is lower than expected seqnum 255'
    if p[:2] == [ 'Logon', 'seqnum' ] and p[3:8] == 'is lower than expected seqnum'.split(' '):
        clientNum, gateNum = int( p[-1] ), 0
        seqnumutil.setSeqNums( clientNum, gateNum )
        seqnumutil.resetSeqNums( sessionID )

    #MsgSeqNum too low, expecting 543 but received 235
    elif p[:3] == [ 'MsgSeqNum', 'too', 'low,' ] and p[3] == 'expecting':
        clientNum, gateNum = int( p[4] ), 0
        seqnumutil.setSeqNums( clientNum, gateNum )
        seqnumutil.resetSeqNums( sessionID )                

class Application( quickfix.Application ):

    def onCreate(self, sessionID):
        logger.debug('onCreate')
        self._sessionID = sessionID
        self._session   = quickfix.Session.lookupSession( sessionID )
    
    def getSessionID(self):
        return self._sessionID

    def getSession(self):
        return self._session
    
    def onLogon(self, sessionID ):
        libreport.reportInfo(subject='FIX LOGIN', txt='Argus has logged in' )
        logger.debug('onLogon')

    def onLogout(self, sessionID ):
        libreport.reportError(subject='FIX LOGOUT', txt='Argus has logged out' )
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
            resetSeqNum( sessionID, message )

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
        # logger.debug( 'fix.new  enter' )
        msg = fut.form_NewOrder( 
            timeInForce = timeInForce, 
            orderId     = orderId, 
            symbol      = symbol, 
            qty         = qty, 
            price       = price,
            tagVal      = tagVal )
        
        session = self.getSession()        
        session.sendToTarget( msg )
        logger.debug( 'fix.new  id=%s s=%-4s q=%4d p=%f' % ( orderId, symbol, qty, price ), neverPrint=True )

    def cancelOrder( self, orderId, origOrderId, symbol, qty, tagVal=None ):
        # logger.debug( 'fix.cx   enter', neverPrint=True )
            
        msg = fut.form_Cancel( 
            orderId     = orderId, 
            origOrderId = origOrderId,
            symbol      = symbol, 
            qty         = qty,
            tagVal      = tagVal )
        
        session = self.getSession()        
        session.sendToTarget( msg )
        
class AppThread( threading.Thread ):
    
    def __init__(self, app, cfgpath, loop=False ):
        super( AppThread, self).__init__()        
        self._app   = app
        self._loop  = loop        
        self._file  = cfgpath
        
    def run( self ):
        
        try:            
            settings    = quickfix.SessionSettings( self._file )
            storeFactory= quickfix.FileStoreFactory( settings )
            logFactory  = quickfix.FileLogFactory( settings )
            initiator   = quickfix.SocketInitiator( self._app, storeFactory, settings, logFactory )
            initiator.start()
            
        except (quickfix.ConfigError, quickfix.RuntimeError), _e:
            logger.error( traceback.format_exc() )

def sendOrder( app, orderId, symbol, qty, price, timeInForce, tagVal=None ):
    logger.debug( 'fix.lnk.new  enter', neverPrint=True )
        
    msg = fut.form_NewOrder( 
        timeInForce = timeInForce, 
        orderId     = orderId, 
        symbol      = symbol, 
        qty         = qty, 
        price       = price,
        tagVal      = tagVal )
    
    session = app.getSession()        
    session.sendToTarget( msg )

def cancelOrder( app, orderId, origOrderId, symbol, qty ):
    logger.debug( 'fix.lnk.cx  enter', neverPrint=True )
        
    msg = fut.form_Cancel( 
        orderId     = orderId, 
        origOrderId = origOrderId,
        symbol      = symbol, 
        qty         = qty )
    
    session = app.getSession()        
    session.sendToTarget( msg )

def _initFixConfig():
    '''
    needs tweak: fix_connConfig
    '''
    
    comm    = twval.getenv( 'fix_connConfig' )
    host, port, sender, target = comm[ 'host' ], comm[ 'port' ], comm[ 'sender' ], comm[ 'target' ]
        
    fixDictPath = environment.getDataRoot( 'fixdict')
    logPath     = fixccfg.getFIXConfig( 'log'    )
    storePath   = fixccfg.getFIXConfig( 'store'  )
    
    content = fixccfg.configContent( 
        fixDictPath=fixDictPath, logPath=logPath, storePath=storePath, host=host, port=port, sender=sender, target=target 
    )    
    return fixccfg.createConfigFile( content )
    
def init():
    '''
    with twcx.Tweaks(
        fix_root=os.path.join( logger.dirName(), 'fix' ),
        fix_connConfig={ 'host': 9999, 'port': '10.1.1.230', 'sender': 'CLIENT1', 'target': 'IREACH' } ):
    '''
    cfgpath = _initFixConfig()
        
    app     = Application( )    
    thread  = AppThread( app=app, cfgpath=cfgpath )    
    thread.start()
    return app, thread

