'''
author: 'ilya'
'''

import os
import glob
import numpy
import datetime
import cPickle as pickle
import robbie.fix.util as fut
import robbie.fix.tag as fixtag

tag2name = dict( (int(n),v) for (n,v) in fixtag._tag2name.iteritems() if n != '58' )

quadLogRoot    = r'C:\Users\ilya\GenericDocs\dev\quad\data\fix-logs'

Name_ExecType  = tag2name[fut.Tag_ExecType]
Name_MsgType   = tag2name[fut.Tag_MsgType]
Name_OrderType = tag2name[fut.Tag_OrderType]
Name_Account   = tag2name[fut.Tag_Account]
Name_Side      = tag2name[fut.Tag_Side]

names = dict((
    ( 'CumQty',         int),
    ( 'ExecTransType',  str),
    ( 'ExecType',       str),
    ( 'LastShares',     int),
    ( 'LeavesQty',      int),
    ( 'MsgType',        str),
    ( 'OrdStatus',      str),
    ( 'OrderQty',       int),
    ( 'OrderType',      str),
    ( 'Price',          float),
    ( 'Side',           str),
    ( 'Symbol',         str),
    ( 'SendingTime',    str),
))

def _nameConvert(data):
    d1 = dict( (tag2name[n],v) for n,v in data.iteritems() if n in tag2name )
    # import pdb; pdb.set_trace()
    d2 = dict( (n, names[n](v)) for n,v in d1.iteritems() if n in names )
    return d2

def nameConvert(data):
    if isinstance(data, list):
        return [ _nameConvert(d) for d in data ]
    else:
        return _nameConvert(data)

def showGroups1():
    hh  = {}
    files = glob.glob( os.path.join(d, '*.log'))
    for pix, p in enumerate(files):
        print '%2d' % pix, p
        h  = parse(p, groupBy = 'HM')
        for n0,v0 in h.iteritems():
            for n1,v1 in v0.iteritems():
                if n0 not in hh:
                    hh[n0] = {}
                if n1 not in hh[n0]:
                    hh[n0][n1] = []
                hh[ n0 ][ n1 ].append(v1)
    ns0 = sorted(hh.keys())
    for n0 in ns0:
        v0 = hh[ n0 ]
        print '-------------------------------------------'
        print n0
        print '==========================================='
        ns1 = sorted( v0.keys() )
        for n1 in ns1:
            a = v0[ n1 ]
            if numpy.max( a ) < 100:
                continue
            print '%10s %5.0f %5.0f %5.0f' % ( n1, numpy.mean( a ), numpy.max( a ), numpy.std( a ) )

def parse(path, groupBy='HM'):
    ''' HM = groupby hour and minute '''
    h = {}
    with open(path) as fd:
        for l in fd:
            data = l.split( chr(1) )[:-1]
            head = data[0]
            ts   = head[:21]
            try:
                data = dict( (int(n),v) for d in data[1:] for (n,v) in [d.split('=')])
            except:
                try:
                    data = dict( (int(n),v) for d in data[1:] if not d.startswith('58') for (n,v) in [ d.split('=') ] )
                except:
                    print '!!', data
                    continue
            if data[ fut.Tag_MsgType ] in ('A', '0', '1', '2', '3', '4', '5' ):
                continue
            dt   = datetime.datetime.strptime(ts, '%Y%m%d-%H:%M:%S.%f')
            k    = (dt.hour, dt.minute)
            if groupBy == 'HM':
                try:
                    tag = fut.Tag_ExecType
                    kk  = data[ tag ]
                except:
                    try:
                        tag = fut.Tag_OrderType
                        kk  = data[ tag ]
                    except:
                        print '--->', data
                        continue
            elif groupBy == 'ACCOUNT':
                try:
                    tag = fut.Tag_Account
                    kk  = data[ tag ]
                except:
                    print '!!', data
                    continue
            else:
                raise ValueError('Unknown groupBy=%s' % groupBy )
            if groupBy in ('HM',):
                if kk not in h:
                    h[kk] = {}
                if k not in h[kk]:
                    h[kk][k] = 0
                h[kk][k] += 1
            elif groupBy in ('ACCOUNT',):
                if kk not in h:
                    h[kk] = []
                h[kk].append( data )
            else:
                raise ValueError('Uknown groupBy=%s' % groupBy)
        return dict(h)

def combineData(root, fn):
    files    = sorted(glob.glob( os.path.join(quadLogRoot, '*.log')))
    e        = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    pathRoot = os.path.join(root, fn, e)
    os.makedirs(pathRoot)

    hh = {}
    NX = 10
    for pix, p in enumerate(files):
        print '%2d' % pix, p
        h  = parse(p, groupBy = 'ACCOUNT')
        for trader,v in h.iteritems():
            # import pdb; pdb.set_trace()
            if trader not in hh:
                hh[ trader ] = []
            allv = hh[ trader ]
            allv.extend(v)

        if pix and (pix % NX) == 0:
            for trader,v in hh.iteritems():
                path = os.path.join(pathRoot,'%s.pkl' % trader )
                if os.path.exists(path):
                    with open(path) as fd:
                        th = pickle.load(fd)
                else:
                    th = []
                thl = len(th)
                th.extend(v)
                with open(path, 'w') as fd:
                    pickle.dump(th,fd)
                print '%20s %8d %8d' % (trader, thl, len(th))
            hh = {}
    if hh:
        for trader,v in hh.iteritems():
            path = os.path.join(pathRoot,'%s.pkl' % trader )
            if os.path.exists(path):
                with open(path) as fd:
                    th = pickle.load(fd)
            else:
                th = []
            thl = len(th)
            th.extend(v)
            with open(path, 'w') as fd:
                pickle.dump(th,fd)
            print '%20s %8d %8d' % (trader, thl, len(th))

def main():
    combineData(r'c:\temp', 'accounts')

if __name__ == '__main__':
    main()

