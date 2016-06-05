import sys
import time
import quickfix as fix

class Application(fix.Application):
    orderID = 0
    execID = 0

    def onCreate(self, sessionID):
        print 'onCreate sessionID=%s' % sessionID
        # self._sessionID = sessionID
        # self._session   = fix.Session.lookupSession( sessionID )
        # print 'onCreate self._session=%s' % self._session

    def getSessionID(self):
        return self._sessionID

    def getSession(self):
        return self._session

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

try:
    file            = r'c:\users\ilya\GenericDocs\dev\data\margot\20160531\fix\config\fixconnect.cfg'

    settings        = fix.SessionSettings( file )
    application     = Application()
    storeFactory    = fix.FileStoreFactory( settings )
    logFactory      = fix.ScreenLogFactory( settings )
    initiator       = fix.SocketInitiator(application, storeFactory, settings, logFactory )
    initiator.start()
    while 1:
        time.sleep(1)

except (fix.ConfigError, fix.RuntimeError) as e:
	print(e)


'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\fix\initiator.py
'''