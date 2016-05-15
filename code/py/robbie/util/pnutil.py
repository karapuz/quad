__author__ = 'ilya'

def calcPnl(q,e, qtyField = 'qty', priceField = 'price'):
    '''  q = {'Buy': [], 'Sell':[] } '''
    pnl    = []
    if not e[qtyField]:
        return pnl
    while e[qtyField]:
        e_qty  = abs(e[qtyField])
        if e[qtyField] > 0:
            if not q['Sell']:
                q['Buy'].append( e )
                break
            else:
                sell = q['Sell'].pop(0)
                sell_qty = abs(sell[qtyField])
                if sell_qty >= e_qty:
                    # new order is consumed fully
                    qty            = e_qty
                    e[qtyField]    = 0
                    sell[qtyField] = e_qty - sell_qty
                    if sell[qtyField]:
                        q['Sell'].insert(0,sell)
                if sell_qty < e_qty:
                    # new order is consumed partially
                    qty         = sell_qty
                    # proper sign - it was a Buy order offset with Sell - must be positive
                    e[qtyField] = e_qty - sell_qty
                # pnl.append( (qty * (sell[priceField] - e[priceField]), ( qty, sell[priceField], e[priceField]) ))
                pnl.append( qty * (sell[priceField] - e[priceField]) )
        else:
            if not q['Buy']:
                q['Sell'].append( e )
                break
            else:
                buy = q['Buy'].pop(0)
                buy_qty = abs(buy[qtyField])
                if buy_qty >= e_qty:
                    # new order is consumed fully
                    qty            = e_qty
                    e[qtyField]    = 0
                    buy[qtyField]  = buy_qty - e_qty
                    if buy[qtyField]:
                        q['Buy'].insert(0,buy)
                if buy_qty < e_qty:
                    # new order is consumed partially
                    qty         = buy_qty
                    # proper sign - it was a Buy order offset with Sell - must be positive
                    e[qtyField] = buy_qty - e_qty
                # pnl.append( (qty * (e[priceField] - buy[priceField]), ( qty, e[priceField], buy[priceField] ) ) )
                pnl.append( qty * (e[priceField] - buy[priceField]))
    return pnl

qtyField   = 'qty'
priceField = 'price'
def test_1():

    v   = [
            { qtyField:  5, 's': 'AAPL', priceField: 10.0 },
            { qtyField:  5, 's': 'AAPL', priceField: 10.0 },
            { qtyField:-10, 's': 'AAPL', priceField: 15.0 },
    ]
    q   = {'Buy':[], 'Sell':[]}
    pnl = []
    for e in v:
        pnl.append(calcPnl(q,e,qtyField=qtyField, priceField = priceField))
    assert [[], [], [25.0, 25.0]] == pnl
    return pnl

def test_2():
    qtyField   = 'qty'
    priceField = 'price'
    v   = [
            { qtyField:  5, 's': 'AAPL', priceField: 10.0 },
            { qtyField:  5, 's': 'AAPL', priceField: 10.0 },
            { qtyField: -6, 's': 'AAPL', priceField: 15.0 },
            { qtyField: -4, 's': 'AAPL', priceField: 15.0 },
    ]
    q   = {'Buy':[], 'Sell':[]}
    pnl = []
    for e in v:
        pnl.append(calcPnl(q,e,qtyField=qtyField, priceField = priceField))
    assert [[], [], [25.0, 5.0], [20.0]] == pnl
    return pnl

def test_3():
    v   = [
            { qtyField:  5, 's': 'AAPL', priceField: 15.0 },
            { qtyField:  5, 's': 'AAPL', priceField: 15.0 },
            { qtyField: -6, 's': 'AAPL', priceField: 15.0 },
            { qtyField: -4, 's': 'AAPL', priceField: 15.0 },
    ]
    q   = {'Buy':[], 'Sell':[]}
    pnl = []
    for e in v:
        pnl.append(calcPnl(q,e,qtyField=qtyField, priceField = priceField))
    assert [[], [], [0.0, 0.0], [0.0]] == pnl
    return pnl

def test_4():
    v   = [
            { qtyField: -6, 's': 'AAPL', priceField: 15.0 },
            { qtyField: -4, 's': 'AAPL', priceField: 15.0 },
            { qtyField:  5, 's': 'AAPL', priceField: 10.0 },
            { qtyField:  5, 's': 'AAPL', priceField: 10.0 },
    ]
    q   = {'Buy':[], 'Sell':[]}
    pnl = []
    for e in v:
        pnl.append(calcPnl(q,e,qtyField=qtyField, priceField = priceField))
    assert [[], [], [25.0], [5.0, 20.0]] == pnl
    return pnl

def test_5():
    v   = [
            { qtyField: -6, 's': 'AAPL', priceField: 10.0 },
            { qtyField: -4, 's': 'AAPL', priceField: 10.0 },
            { qtyField:  5, 's': 'AAPL', priceField: 15.0 },
            { qtyField:  5, 's': 'AAPL', priceField: 15.0 },
    ]
    q   = {'Buy':[], 'Sell':[]}
    pnl = []
    for e in v:
        pnl.append(calcPnl(q,e,qtyField=qtyField, priceField = priceField))
    assert [[], [], [-25.0], [-5.0, -20.0]] == pnl
    return pnl

'''
import robbie.util.pnutil as p
v = [
        { qtyField: 10, 's': 'AAPL', priceField: 10.0 },
        { qtyField:-10, 's': 'AAPL', priceField: 15.0 },
        { qtyField: 10, 's': 'AAPL', priceField: 10.0 },
        { qtyField: 10, 's': 'AAPL', priceField: 10.0 },
        { qtyField:-10, 's': 'AAPL', priceField: 15.0 },
        { qtyField: -5, 's': 'AAPL', priceField: 15.0 },
        { qtyField: -5, 's': 'AAPL', priceField: 15.0 },
]
q = {'Buy':[], 'Sell':[]}

e = { qtyField:  5, 's': 'AAPL', priceField: 10.0 }
p.calcPnl(q,e)

e = { qtyField:  5, 's': 'AAPL', priceField: 10.0 }
p.calcPnl(q,e)

e = { qtyField:-10, 's': 'AAPL', priceField: 15.0 }
p.calcPnl(q,e)
'''

import os
import datetime
import cPickle as pickle

def load(root, fn):
    path = os.path.join(root, fn)
    with open(path) as fd:
        d = pickle.load(fd)
    return d

def pnlPerInstr( dataList ):
    for data in dataList:
        pass