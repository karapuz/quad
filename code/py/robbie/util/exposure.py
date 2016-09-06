'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.strat module
DESCRIPTION : this module contains strategies
'''

import os
from   robbie.util.logging import logger

def dumpIntoCsv(exposure, path, rowSep='\n', cellSep=','):
    ''' loadFromCsv '''
    with open(path, 'w') as fd:
        row = ['Target', 'Owner', 'Symbol', 'Shares', 'AvgPrice']
        fd.write( cellSep.join(row) + rowSep)
        for (owner, rows) in exposure.iteritems():
            for e in rows:
                target, symbol, shares, avgPrice = e
                row = [target, owner, symbol, str(shares), str(avgPrice)]
                logger.debug('row = %s', str(cellSep.join(row)))
                fd.write( cellSep.join(row) + rowSep)

def loadFromCsv(path):
    ''' loadFromCsv '''
    rowSep      = '\n'
    cellSep     = ','
    exposure    = {}

    with open(path, 'r') as fd:
        txt = fd.read()
        for ix,row in enumerate(txt.split(rowSep)):
            if not row:
                continue
            cells = row.split(cellSep)
            if ix == 0:
                header = cells
                continue
            target, owner, symbol, shares, avgPrice = cells
            if owner not in exposure:
                exposure[ owner ] = []
            exposure[ owner ].append( (target, symbol, int(shares), float(avgPrice)) )
        return exposure

def uploadIntoStrip(agent, exposure, strat, op='replace'):
    ''' uploadIntoStrip
    exposure[ owner ]:
        -> target, symbol, int(shares), float(avgPrice)
    '''
    if agent not in exposure:
        logger.debug('uploadIntoStrip: no such owner=%s', agent)
        return
    for target in ('SRC', 'SNK'):
        orderStrip = strat.getTargetOrderState(target=target)
        for (trgt, symbol, shares, avgPrice) in exposure[ agent ]:
            if target == trgt:
                ix = orderStrip.getIxByTag( symbol )
                if op == 'replace':
                    orderStrip._realized[ ix ] = shares
                elif op == 'add':
                    orderStrip._realized[ ix ] += shares
                else:
                    raise ValueError('Uknown exposure update op=%s' % op)
                logger.debug('uploadIntoStrip: symbol=%5s shares=%5s avgPrice=%8s', symbol, shares, avgPrice)

def collecFromStrip(agent, strat):
    ''' uploadIntoStrip
    exposure[ owner ]:
        -> target, symbol, int(shares), float(avgPrice)
    '''
    exposure = { agent: [] }
    avgPrice = -1
    for target in ('SRC', 'SNK'):
        orderStrip = strat.getTargetOrderState(target=target)
        for symbol in orderStrip._symbols:
                ix      = orderStrip.getIxByTag( symbol )
                shares  = orderStrip.getRealizedByIx( ix )
                if shares:
                    exposure[ agent ].append( (target, symbol, int(shares), avgPrice) )
    return exposure