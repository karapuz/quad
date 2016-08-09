'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.execsrc module
'''

import zmq
import json
import time
import argparse
import robbie.fix.util as fut
import robbie.echo.stratutil as stratutil
import robbie.echo.sourcecore as sourcecore
from   robbie.echo.stratutil import STRATSTATE

import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.execution.util as executil
import robbie.execution.execsrclink as execsrclink
import robbie.execution.messageadapt as messageadapt

import robbie.util.pricestriputil as pricestriputil

def getMarketPrices(priceStrip, symbol):
    ''' get Market Prices  '''
    if priceStrip is None:
        return {}

    trade   = priceStrip.getInstantPriceByName(priceType='TRADE', symbol=symbol)
    bid     = priceStrip.getInstantPriceByName(priceType='BID', symbol=symbol)
    ask     = priceStrip.getInstantPriceByName(priceType='ASK', symbol=symbol)
    return {symbol: {'TRADE': trade, 'BID': bid, 'ASK': ask}}

def run_execsrc():
    # prepare fix
    # Prepare our context and sockets
    context     = zmq.Context()
    turf        = twkval.getenv('run_turf')
    agt_comms   = turfutil.get(turf=turf, component='communication')
    agt_list    = turfutil.get(turf=turf, component='agents')

    signalMode  = turfutil.get(turf=turf, component='signal')

    poller      = zmq.Poller()

    cmd_port    = agt_comms['SRC_CMD']['port_cmd']
    cmdConn     = context.socket(zmq.REP)
    cmdConn.bind("tcp://*:%s" % cmd_port)
    poller.register(cmdConn, zmq.POLLIN)

    reg_port    = agt_comms['SRC_REG']['port_reg']
    regConn     = context.socket(zmq.REP)
    regConn.bind("tcp://*:%s" % reg_port)
    poller.register(regConn, zmq.POLLIN)

    rediPort     = agt_comms['REDI']['port_cmd']
    rediCon      = context.socket(zmq.PAIR)
    rediCon.bind('tcp://*:%s' % rediPort)
    poller.register(rediCon, zmq.POLLIN)

    conns   = {}
    sigs    = []
    for agent, agt_comm in agt_comms.iteritems():
        if agent not in agt_list:
            logger.debug('EXECSRCAPP: not an agent: %s', agent)
            continue
        logger.debug( 'EXECSRCAPP: Agent=%s', agent)
        port_execSrc    = agt_comm['agent_execSrc']
        port_sigCon     = agt_comm['agent_sigCon']

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port_execSrc)
        conns[agent] = c

        c = context.socket(zmq.PUB)
        c.bind('tcp://*:%s' % port_sigCon)
        sigs.append( c )

    bbg = pricestriputil.createPriceStrip(turf=turf, readOnly=True)
    #bbg = None

    signalStrat = sourcecore.SourceStrat(conns,mode=signalMode)
    msgAdapter  = messageadapt.Message(['ECHO1','ECHO1'], 'TIME')
    appShell, _ = execsrclink.init(
                    tweakName   = 'fix_SrcConnConfig',
                    signalStrat = signalStrat,
                    mode        = signalMode,
                    pricestrip  = bbg,
                    msgAdapter  = msgAdapter)
    app         = appShell.getApplication()

    while True:
        logger.debug('in the loop')
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if rediCon in socks:
            msgs    = rediCon.recv()
            data    = json.loads(msgs)
            logger.debug('EXECSRCAPP: REDI = %s', data)

            action      = str(data['action'])
            orderType   = str(data['orderType'])
            signalName  = str(data['signalName'])
            execTime    = str(data['execTime'])
            orderId     = str(data['orderId'])
            symbol      = str(data['symbol'])
            qty         = int(data['qty'])
            mktPrice    = getMarketPrices(bbg, symbol=symbol)

            if action == STRATSTATE.ORDERTYPE_NEW:
                price   = data['price']
                signalStrat.onNew(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price, orderType=orderType, mktPrice=mktPrice)

            elif action == STRATSTATE.ORDERTYPE_NEW:
                price   = data['price']
                signalStrat.onFill(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, price=price, mktPrice=mktPrice)

            elif action == STRATSTATE.ORDERTYPE_CXRX:
                origOrderId = data['origOrderId']
                signalStrat.onCxRx(signalName=signalName, execTime=execTime, orderId=orderId, symbol=symbol, qty=qty, origOrderId=origOrderId, mktPrice=mktPrice)

            else:
                raise ValueError('Unknown action=%s' % action)

            rediCon.send(orderId)
            continue

        if regConn in socks:
            msg = regConn.recv()
            regConn.send('OK')
            logger.debug('EXECSRCAPP: REGISTERED[SRC] = %s', msg)
            continue

        if cmdConn in socks:
            msgs    = cmdConn.recv()
            msg     = json.loads(msgs)
            msg     = executil.toStr(msg)
            cmd     = msg['cmd']
            logger.debug('EXECSRCAPP: CMD=%s', msg)
            cmdConn.send('RECEIVED')

            if cmd == 'KILL':
                for c in sigs:
                    c.send( cmd ) # process task
                time.sleep(10)
                break

            elif cmd == 'SEND':
                agent   = msg['agent']
                symbol  = msg.get('symbol', 'IBM')
                price   = float(msg.get('price','200'))
                qty     = int(msg.get('qty','1000'))
                app.sendOrder(
                    senderCompID = 'BANZAI',
                    targetCompID = 'FIXIMULATOR',
                    account      = agent,
                    orderId      = stratutil.newOrderId('SRC'),
                    symbol       = symbol,
                    qty          = qty,
                    price        = price,
                    timeInForce  = fut.Val_TimeInForce_DAY,
                    tagVal       = None )

            elif cmd == 'CX':
                agent         = msg['agent']
                origOrderId   = msg['origOrderId']
                if 'qty' in msg:
                    qty = int(msg['qty'])
                else:
                    qty = None
                symbol        = msg.get('sybol', 'IBM')
                app.cancelOrder(
                    senderCompID = 'BANZAI',
                    targetCompID = 'FIXIMULATOR',
                    account      = agent,
                    orderId      = stratutil.newOrderId('CX_SRC'),
                    symbol       = symbol,
                    qty          = qty,
                    origOrderId  = origOrderId)

            else:
                logger.error('EXECSRCAPP: Unknown cmd=%s', cmd)

            continue

if __name__ == '__main__':
    '''
    -T turf
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    args    = parser.parse_args()
    turf    = args.turf
    logger.debug( 'agent: turf=%s', turf)

    fix_SrcConnConfig   = turfutil.get(turf=turf, component='fix_SrcConnConfig')
    fix_SinkConnConfig  = turfutil.get(turf=turf, component='fix_SinkConnConfig')

    tweaks  = {
        'run_turf'          : turf,
        'run_domain'        : 'echo_source',
        'fix_SrcConnConfig' : fix_SrcConnConfig,
        'fix_SinkConnConfig': fix_SinkConnConfig,
    }

    with twkcx.Tweaks( **tweaks ):
        run_execsrc()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\execsrcapp.py --turf=dev_quad

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\execsrcapp.py --turf=dev_full
'''
