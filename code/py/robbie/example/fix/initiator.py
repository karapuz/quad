import sys
import time
import quickfix as fix
import robbie.fix.util as fut

class Application(fix.Application):
    orderID = 0
    execID  = 0

    def __init__(self):
        super(Application,self).__init__()
        self._session = 'SESSION!'

    def onCreate(self, sessionID):
        self._session   = fix.Session.lookupSession( sessionID )
        print 'onCreate session =', self._session

    def onLogon(self, sessionID):
        self._session   = fix.Session.lookupSession( sessionID )
        print 'onLogon session =', self._session

    def getSession(self):
        return self._session

    def onLogout(self, sessionID):
        print 'onLogout sessionID =', sessionID
        return

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

def sendOrder( app, orderId, symbol, qty, price, timeInForce, tagVal=None ):
    print 'fix.lnk.new  enter'

    msg = fut.form_NewOrder(
        senderCompID = 'BANZAI',
        targetCompID = 'FIXIMULATOR',
        timeInForce = timeInForce,
        orderId     = orderId,
        symbol      = symbol,
        qty         = qty,
        price       = price,
        tagVal      = tagVal )

    session = app.getSession()
    print 'session =', session
    print msg
    session.sendToTarget( msg )
'''
<20160604-00:37:59, FIX.4.2:FIXIMULATOR->BANZAI, incoming>
(
8=FIX.4.2
9=136
35=D
34=2
49=BANZAI
52=20160604-00:37:59.525
56=FIXIMULATOR
11=1465000679352
21=1
38=100
40=1
54=1
55=IBM
59=0
60=20160604-00:37:59.500
10=079
)
8=FIX.4.2
9=126
35=D
49=BONZAI
56=FIXIMULATOR
1=TEST_Account
11=1
15=USD
21=2
38=1000
40=2
44=200.0
54=1
55=IBM
59=0
60=20160604-00:34:17.085
10=109
'''
try:
    file            = r'c:\users\ilya\GenericDocs\dev\data\margot\20160531\fix\config\fixconnect.cfg'

    settings        = fix.SessionSettings( file )
    application     = Application()
    storeFactory    = fix.FileStoreFactory( settings )
    logFactory      = fix.ScreenLogFactory( settings )
    initiator       = fix.SocketInitiator(application, storeFactory, settings, logFactory )
    initiator.start()

    time.sleep(5)

    sendOrder(
        app         = application,
        orderId     = '1',
        symbol      = 'IBM',
        qty         = 1000,
        price       = 200,
        timeInForce = fut.Val_TimeInForce_DAY,
        tagVal      = None )

    while 1:
        time.sleep(1)


except (fix.ConfigError, fix.RuntimeError) as e:
	print(e)
