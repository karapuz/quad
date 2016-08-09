import time
import robbie.fix.util as fut
import robbie.echo.sourcecore as sourcecore
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
import robbie.execution.execsrclink as execsrclink
import robbie.execution.messageadapt as messageadapt

def sendOrder( app, account, orderId, symbol, qty, price, timeInForce = fut.Val_TimeInForce_DAY, tagVal=None ):
    print 'fix.lnk.new  enter'
    msg = fut.form_NewOrder(
        senderCompID = 'BANZAI',
        targetCompID = 'FIXIMULATOR',
        account      = account,
        timeInForce  = timeInForce,
        orderId      = orderId,
        symbol       = symbol,
        qty          = qty,
        price        = price,
        tagVal       = tagVal )

    session = app.getSession()
    print 'session =', session
    print msg
    session.sendToTarget( msg )

if __name__ == '__main__':
    with twkcx.Tweaks(run_turf='dev'):
        sig2comm    = { 'PRESMAN': messageadapt.Communication() }
        signalStrat = sourcecore.SourceStrat(sig2comm)
        msgAdapter  = messageadapt.Message(['A','B'], 'TIME')
        thread, application = execsrclink.init(signalStrat, msgAdapter)
    # print application
    time.sleep(5)
    sendOrder(
        app     = application,
        orderId = 'ORDER1',
        account = 'ECHO1',
        symbol  = 'IBM',
        qty     = 1000,
        price   = 200)

    while 1:
        # print '.'
        time.sleep(1)
'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\example\driver\execsrcdriver.py
'''