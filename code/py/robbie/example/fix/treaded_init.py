import sys
import time
import threading
import quickfix as fix

class Application(fix.Application):
	orderID = 0
	execID = 0

	def onCreate(self, sessionID): return
	def onLogon(self, sessionID): return
	def onLogout(self, sessionID): return
	def toAdmin(self, sessionID, message): return
	def fromAdmin(self, sessionID, message): return
	def toApp(self, sessionID, message): return
	def fromApp(self, message, sessionID):
		beginString = fix.BeginString()
		msgType = fix.MsgType()
		message.getHeader().getField( beginString )
		message.getHeader().getField( msgType )
	
		symbol      = fix.Symbol()
		side        = fix.Side()
		ordType     = fix.OrdType()
		orderQty    = fix.OrderQty()
		price       = fix.Price()
		clOrdID     = fix.ClOrdID()

		message.getField( ordType )
		if ordType.getValue() != fix.OrdType_LIMIT:
			raise fix.IncorrectTagValue( ordType.getField() )

		message.getField( symbol )
		message.getField( side )
		message.getField( orderQty )
		message.getField( price )
		message.getField( clOrdID )

		executionReport = fix.Message()
		executionReport.getHeader().setField( beginString )
		executionReport.getHeader().setField( fix.MsgType(fix.MsgType_ExecutionReport) )

		executionReport.setField( fix.OrderID(self.genOrderID()) )
		executionReport.setField( fix.ExecID(self.genExecID()) )
		executionReport.setField( fix.OrdStatus(fix.OrdStatus_FILLED) )
		executionReport.setField( symbol )
		executionReport.setField( side )
		executionReport.setField( fix.CumQty(orderQty.getValue()) )
		executionReport.setField( fix.AvgPx(price.getValue()) )
		executionReport.setField( fix.LastShares(orderQty.getValue()) )
		executionReport.setField( fix.LastPx(price.getValue()) )
		executionReport.setField( clOrdID )
		executionReport.setField( orderQty )

		if beginString.getValue() == fix.BeginString_FIX40 or beginString.getValue() == fix.BeginString_FIX41 or beginString.getValue() == fix.BeginString_FIX42:
			executionReport.setField( fix.ExecTransType(fix.ExecTransType_NEW) )

		if beginString.getValue() >= fix.BeginString_FIX41:
			executionReport.setField( fix.ExecType(fix.ExecType_FILL) )
			executionReport.setField( fix.LeavesQty(0) )

		try:
			fix.Session.sendToTarget( executionReport, sessionID )
		except fix.SessionNotFound as e:
			return

	def genOrderID(self):
		self.orderID = self.orderID+1
		return self.orderID

	def genExecID(self):
		self.execID = self.execID+1
		return self.execID

class AppThread( threading.Thread ):
    def __init__(self, app, cfgpath, loop=False ):
        super( AppThread, self).__init__()
        self._app   = app
        self._loop  = loop
        self._file  = cfgpath
        print 'cfgpath = %s' % cfgpath

    def run( self ):
        try:
            self._settings        = fix.SessionSettings( self._file )
            self._storeFactory    = fix.FileStoreFactory( self._settings )
            self._logFactory      = fix.ScreenLogFactory( self._settings )
            self._initiator       = fix.SocketInitiator(self._app, self._storeFactory, self._settings, self._logFactory )
            self._initiator.start()

        except (fix.ConfigError, fix.RuntimeError) as e:
            print(e)

if __name__ == '__main__':

    cfgpath = r'c:\users\ilya\GenericDocs\dev\data\margot\20160531\fix\config\fixconnect.cfg'
    app = Application()
    t = AppThread( app=app, cfgpath=cfgpath)
    t.start()
    t.join()
    #run()
    while 1:
        print '.'
        time.sleep(1)
