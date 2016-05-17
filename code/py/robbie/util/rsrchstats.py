__author__ = 'ilya'

'''
   'OrdStatus' == 'ExecType': {
        '0': 'New',
        '4': 'Canceled',
        '5': 'Replaced',
        '7': 'Stopped',
        '8': 'Rejected',
        '9': 'Suspended',
        'C': 'Expired',
    }

    'OrderType' : {
        '1': 'Market',
        '2': 'Limit',
        '3': 'Stop',
        '4': 'StopLimit',
        '5': 'MarketOnClose',
        '6': 'WithOrWithout',
        '7': 'LimitOrBetter',
        '8': 'LimitWithOrWithout',
        '9': 'OnBasis',
        'A': 'OnClose',
        'B': 'LimitOnClose',
        'C': 'ForexMarket',
        'D': 'PreviouslyQuoted',
        'E': 'PreviouslyIndicated',
        'F': 'ForexLimit',
        'G': 'ForexSwap',
        'H': 'ForexPreviouslyQuoted',
        'I': 'Funari',
        'P': 'Pegged',
    },

New:
    {
        'LastShares'    : 0,
        'ExecType'      : '0',
        'OrdStatus'     : '0',
        'LeavesQty'     : 30,
        'OrderType'     : '2',
        'Price'         : 57.69,
        'Symbol'        : 'TEVA',
        'OrderQty'      : 30,
        'CumQty'        : 0,
        'MsgType'       : '8',
        'ExecTransType' : '0',
        'SendingTime'   : '20151001-12:34:08',
        'Side'          : '2'
}

'''
import os
import glob
import cPickle as pickle
import robbie.util.pnutil as pnutil
import robbie.util.config as config
import robbie.util.logfile as logfile

def VQ1(processed=[]):
    ''' OrdStatus != ExecType?
    '''
    quadStratRoot = config.quadStratRoot
    paths    = sorted(glob.glob( os.path.join(quadStratRoot, '*.pkl')))
    print paths
    for path in paths:
        if path in processed:
            continue
        processed.append(path)
        print 'path', path
        with open(path) as fd:
            traderData = pickle.load(fd)
        for data in traderData:
            data = logfile.nameConvert(data)
            go = True
            exempt = ( data['OrdStatus'] == '0' )

            if not exempt:
                for k in ['ExecType', 'OrdStatus']:
                    if k not in data:
                        print '[VQ1:1]', data
                        go = False
                        break
                if go and data['ExecType'] != data['OrdStatus']:
                    print '[VQ1:2]', data
                    continue

import collections, datetime
from   robbie.util.logging import logger
def VQ2(processed=[]):
    ''' OrdStatus != ExecType?
    '''
    quadStratRoot = config.quadStratRoot
    paths    = sorted(glob.glob( os.path.join(quadStratRoot, '*.pkl')))[:10]
    print paths
    hh       = collections.defaultdict(dict)
    for path in paths:
        if path in processed:
            continue
        processed.append(path)
        logger.debug( 'path %s', path )
        with open(path) as fd:
            traderData = pickle.load(fd)

        for data in traderData:
            data = logfile.nameConvert(data)
            # SendingTime: '20151207-20:29:05'
            dt  = datetime.datetime.strptime(data['SendingTime'], '%Y%m%d-%H:%M:%S')
            k   = data['OrdStatus']
            kk  = (dt.hour, dt.minute)
            if kk not in hh[k]:
                hh[k][kk] = 0
            hh[k][kk] += 1
    ks = sorted(hh.iteritems())
    for k,v in ks:
        v = hh[k]
        print '-----------------------------------------\nOrdStatus %s', k
        kks = sorted(v.keys())
        for kk in kks:
            vv = v[kk]
            if vv > 600:
                print '\t%20s : %d' %( kk, vv )

def VQ3(processed=[]):
    ''' OrdStatus != ExecType?
    '''
    quadStratRoot = config.quadStratRoot
    paths    = sorted(glob.glob( os.path.join(quadStratRoot, '*.pkl')))[:10]
    print paths
    hh       = collections.defaultdict(dict)
    for path in paths:
        if path in processed:
            continue
        processed.append(path)
        logger.debug( 'path %s', path )
        with open(path) as fd:
            traderData = pickle.load(fd)

        for data in traderData:
            data = logfile.nameConvert(data)
            # SendingTime: '20151207-20:29:05'
            dt  = datetime.datetime.strptime(data['SendingTime'], '%Y%m%d-%H:%M:%S')
            k   = data['OrdStatus']
            kk  = (dt.hour, dt.minute)
            if kk not in hh[k]:
                hh[k][kk] = 0
            hh[k][kk] += 1
    ks = sorted(hh.iteritems())
    for k,v in ks:
        v = hh[k]
        print '-----------------------------------------\nOrdStatus %s', k
        kks = sorted(v.keys())
        for kk in kks:
            vv = v[kk]
            if vv > 600:
                print '\t%20s : %d' %( kk, vv )

'''
'1': 'PartiallyFilled',
'2': 'Filled',

    'Side' : {
        '1': 'Buy',
        '2': 'Sell',
        '3': 'BuyMinus',
        '4': 'SellPlus',
        '5': 'SellShort',
        '6': 'SellShortExempt',
        '7': 'Undisclosed',
        '8': 'Cross',
        '9': 'CrossShort',
    },

'''
import itertools
import numpy
import robbie.util.pnutil as pnutil
import robbie.util.logfile as logfile
tag2name = logfile.tag2name

shortSide = set( ('2','4','5','6',))
buySide   = set( ( '1', '3' ) )

orderTypeMap = {
    '1': 'Market',
    '2': 'Limit',
    '3': 'Stop',
    '4': 'StopLimit',
    '5': 'MarketOnClose',
    '6': 'WithOrWithout',
    '7': 'LimitOrBetter',
    '8': 'LimitWithOrWithout',
    '9': 'OnBasis',
    'A': 'OnClose',
    'B': 'LimitOnClose',
    'C': 'ForexMarket',
    'D': 'PreviouslyQuoted',
    'E': 'PreviouslyIndicated',
    'F': 'ForexLimit',
    'G': 'ForexSwap',
    'H': 'ForexPreviouslyQuoted',
    'I': 'Funari',
    'P': 'Pegged',
}
def orderTypeConv(x):
    return orderTypeMap[x]

ordStatusMap = {
    '0': 'New',
    '1': 'PartiallyFilled',
    '2': 'Filled',
    '3': 'DoneForDay',
    '4': 'Canceled',
    '5': 'Replaced',
    '6': 'PendingCancel',
    '7': 'Stopped',
    '8': 'Rejected',
    '9': 'Suspended',
    'A': 'PendingNew',
    'B': 'Calculated',
    'C': 'Expired',
    'D': 'AcceptedForBidding',
    'E': 'PendingReplace',
}

def ordStatusConv(x):
    return ordStatusMap[x]

fields    = ['Symbol', 'Price', 'AvgPx', 'LastShares', 'Side']

canSkipOrdStatus = set((
            'New',
            'DoneForDay',
            'Canceled',
            'PendingCancel',
            'Stopped',
            'Rejected',
            'Suspended',
            'PendingNew',
            'Expired',
            'AcceptedForBidding',
            'PendingReplace',
))

def vq3(data, symbols=None):
    h    = {}
    pnls = {}
    allOrderTypes = collections.defaultdict(int)
    for d in data:
        d = dict( (tag2name[n],v) for n,v in d.iteritems() if n in tag2name )

        symbol  = d['Symbol']
        if symbols and symbol not in symbols:
            continue

        side = d['Side']
        if side in shortSide:
            sign = -1
        elif side in buySide:
            sign = 1
        else:
            raise ValueError('Uknown side=%s' % side)

        # sign *= -1

        if 'Price' in d:
            price = float(d['Price'])
        else:
            # print d
            # import pdb; pdb.set_trace()
            price = float(d['AvgPx'])

        ordStatus = ordStatusConv(d['OrdStatus'])
        ordQty    = sign * int(d['LastShares'])

        if 'OrderType' in d:
            allOrderTypes[ orderTypeConv(d['OrderType']) ] += 1

        if ordStatus in canSkipOrdStatus:
             continue

        elif ordStatus in ('Calculated','Replaced'):
            continue

        elif ordStatus in ( 'PartiallyFilled', 'Filled' ):
            pass

        else:
            raise ValueError('Uknown ordStats=%s' % ordStatus )

        # print '%20s %20s %20s %20s' % ( ordStatus, orderTypeConv(d['OrderType']), price, ordQty )
        # import pdb; pdb.set_trace()

        e       = { 'qty': ordQty, 'price': price }
        if symbol not in h:
            pnls[ symbol ] = []
            h[ symbol ] = {'Buy':[], 'Sell':[]}
        pnl = pnutil.calcPnl(q=h[symbol],e=e, qtyField='qty', priceField='price')
        if pnl:
            pnls[ symbol ].append( pnl )
        # import pdb; pdb.set_trace()

    print 'q -----'
    for symbol, q in h.iteritems():
        if q['Sell'] or q['Buy']:
            print symbol# , q
    print 'pnls -----'
    pnls_ = []
    for symbol, q in pnls.iteritems():
        pnl = list( itertools.chain( *q ) )
        pnls_.extend(pnl)
        print '%20s %12.2f %8.2f' % ( symbol,numpy.sum( pnl ), numpy.std(pnl) )

    print '%20s %12.2f %8.2f' % ( 'TOTAL', numpy.sum( pnls_ ), numpy.std(pnls_) )

    print allOrderTypes
    return h, pnls

def main():
    d = r'C:\Temp\accounts\20160420_223312'
    import robbie.util.pnutil as p
    # data = p.load(d, 'RT00504121.pkl')
    # data = p.load(d, 'RT00504152.pkl')
    # data = p.load(d, 'RT00504147.pkl')
    data = p.load(d, 'RT00504753.pkl')
    vq3(data)

if __name__ == '__main__':
    main()
