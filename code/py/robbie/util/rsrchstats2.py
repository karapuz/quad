'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.rsrcutil module
'''

import os
import datetime
import robbie.fix.tag as fixtag

tag2name    = fixtag._tag2name
msgTypes    = fixtag._tagVals['MsgType']
orderTypes  = fixtag._tagVals['OrderType']

execTransTypes  = fixtag._tagVals['ExecTransType']
execTypes       = fixtag._tagVals['ExecType']

shortSide = set( ('2','4','5','6',))
buySide   = set( ( '1', '3' ) )

fields    = ['Symbol', 'Price', 'AvgPx', 'LastShares', 'Side']

def parse(path):
    lines = []
    with open(path) as fd:
        for l in fd:
            data = l.split( chr(1) )[:-1]
            head = data[0]
            ts   = head[:21]
            # print data
            try:
                data = dict( (int(n),v) for d in data[1:] for (n,v) in [d.split('=')])
            except:
                try:
                    data = dict( (int(n),v) for d in data[1:] if not d.startswith('58') for (n,v) in [ d.split('=') ] )
                except:
                    print '!!', data
                    continue
            #dt   = datetime.datetime.strptime(ts, '%Y%m%d-%H:%M:%S.%f')
            #k    = (dt.hour, dt.minute)
            lines.append(data)
        return lines

skipTags = set((
    'BodyLength', 'CheckSum', 'ClOrdID', 'ExecID', 'MsgType',
    'SendingTime', 'TargetCompID', 'TransactTime', 'Account', 'MsgSeqNum'
))

def main():
    d = r'C:\Users\ilya\GenericDocs\DateTree\2016\2016_07\2016_07_18'
    f = 'donovan.msgs'
    stypes = set()
    for data in parse(path=os.path.join(d,f)):
        msgType     = msgTypes[ data[35] ]
        orderType   = orderTypes[ data[40] ]
        execTransType   = execTransTypes[ data[20] ]
        execType        = execTypes[ data[150] ]
        d1 = []
        d2 = []
        for t,v in data.iteritems():
            t = str(t)
            if t in tag2name:
                t = tag2name[str(t)]
                if t in skipTags:
                    continue
                d1.append( ( t, v) )
            else:
                d2.append( ( str(t), v) )

        print msgType, orderType, execTransType, execType
        stypes.add( msgType )
    print stypes
if __name__ == '__main__':
    main()


'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\util\rsrchstats2.py

ExecutionReport Limit New PendingCancel
ExecutionReport Limit New Canceled
ExecutionReport Limit New PendingCancel
ExecutionReport Limit New Canceled
ExecutionReport Limit New New
ExecutionReport Limit New PartialFill
ExecutionReport Limit New PartialFill
ExecutionReport Limit New PartialFill
ExecutionReport Limit New PartialFill
ExecutionReport Limit New PartialFill
ExecutionReport Limit New Fill
ExecutionReport Limit New New
ExecutionReport Limit New New
ExecutionReport Limit New PendingCancel
ExecutionReport Limit New Replaced
ExecutionReport Limit New PendingCancel
ExecutionReport Limit New Replaced
ExecutionReport Limit New PendingCancel
ExecutionReport Limit New Replaced
ExecutionReport Limit New PendingCancel
ExecutionReport Limit New Replaced
ExecutionReport Limit New Fill
ExecutionReport Limit New New
ExecutionReport Limit New Fill

'''