'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : agent.agent module
'''

import json
import zmq
import argparse
import robbie.turf.util as turfutil
import robbie.tweak.value as twkval
import robbie.tweak.context as twkcx
from   robbie.util.logging import logger
import robbie.echo.policy as stratpolicy
import robbie.echo.stratutil as stratutil
from   robbie.echo.stratutil import STRATSTATE

def register(context, regPort, agent, logName):
    regConn          = context.socket(zmq.REQ)
    regConn.connect("tcp://localhost:%s" % regPort)
    regConn.send('AGENT: %s: can i?' % agent)
    ok = regConn.recv()
    logger.debug('AGENT: REGISTER: %s, %s', logName, ok)

def run_agent():
    agent            = twkval.getenv('agt_strat')
    turf             = twkval.getenv('run_turf')

    # policy           = stratpolicy.ScaleVenuePolicy( scale=.5, venue='GREY')
    policy           = stratpolicy.ScaleVenueSpring1Policy( scale=.5, venue='GREY')

    signalMode       = turfutil.get(turf=turf, component='signal')
    agt_comm         = turfutil.get(turf=turf, component='communication', sub=agent)

    agent_execSrc    = agt_comm['agent_execSrc']
    port_sigCon      = agt_comm['agent_sigCon']
    agent_execSnkIn  = agt_comm['agent_execSnkIn']
    agent_execSnkOut = agt_comm['agent_execSnkOut']
    agent_BBIn       = agt_comm['agent_BBIn']
    agent_orderCmd   = "ORDER_CMD"

    context           = zmq.Context.instance()

    snkRegPort        = turfutil.get(turf=turf, component='communication', sub='SNK_REG')['port_reg']
    register(context, regPort=snkRegPort, agent=agent, logName='SNK')

    srcRegPort        = turfutil.get(turf=turf, component='communication', sub='SRC_REG')['port_reg']
    register(context, regPort=srcRegPort, agent=agent, logName='SRC')

    agentSrcInCon       = context.socket(zmq.SUB)
    agentSrcInCon.setsockopt(zmq.SUBSCRIBE, b'')
    agentSrcInCon.connect('tcp://localhost:%s' % agent_execSrc)

    sigCon = context.socket(zmq.SUB)
    sigCon.setsockopt(zmq.SUBSCRIBE, b'')
    sigCon.connect('tcp://localhost:%s' % port_sigCon)

    bbCon = context.socket(zmq.SUB)
    bbCon.setsockopt(zmq.SUBSCRIBE, b'')
    bbCon.connect('tcp://localhost:%s' % agent_BBIn)

    agentOrderCon        = context.socket(zmq.PAIR)
    agentOrderCon.bind("inproc://%s" % agent_orderCmd)

    agentSinkOutCon      = context.socket(zmq.PAIR) # PUB
    agentSinkOutCon.bind('tcp://*:%s' % agent_execSnkOut)

    agentSinkInCon       = context.socket(zmq.PAIR) # SUB
    agentSinkInCon.connect('tcp://localhost:%s' % agent_execSnkIn)

    # Initialize poll set
    poller = zmq.Poller()
    poller.register(sigCon,         zmq.POLLIN)
    poller.register(agentSrcInCon,  zmq.POLLIN)
    poller.register(agentSinkInCon, zmq.POLLIN)
    poller.register(agentOrderCon,  zmq.POLLIN)
    poller.register(bbCon,          zmq.POLLIN)

    if signalMode == stratutil.EXECUTION_MODE.NEW_FILL_CX:
        import robbie.echo.onesession as reflectstrat
        echoStrat = reflectstrat.Strategy(agent=agent, policy=policy)
    elif signalMode == stratutil.EXECUTION_MODE.FILL_ONLY:
        import robbie.echo.reflectstrat2 as reflectstrat2
        echoStrat = reflectstrat2.Strategy(agent=agent, policy=policy)
    else:
        raise ValueError('Unknown signalMode=%s' % signalMode)

    while True:
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if agentSrcInCon in socks:
            msg     = agentSrcInCon.recv() # process signal
            cmd     = json.loads(msg)
            action  = cmd[ 'action'   ]
            data    = cmd[ 'data'     ]
            mktPrice= cmd[ 'mktPrice' ]
            logger.debug('AGENT: SRCIN  = %s mktPrice = %s', msg, mktPrice)

            echoStrat.srcPreUpdate(action=action, data=data, mktPrice=mktPrice)
            echoStrat.srcUpdate(action=action, data=data, mktPrice=mktPrice)
            echoStrat.srcPostUpdate(action=action, data=data, mktPrice=mktPrice)

            # we can create signal orders only as a result to signal.
            # so, once done with processing a signal, process resulting orders
            echoStrat.startOrdersToAction()

        if agentSinkInCon in socks:
            msg     = agentSinkInCon.recv() # process task
            cmd     = json.loads(msg)
            action  = cmd['action']
            data    = cmd['data'  ]
            logger.debug('AGENT: SNKIN = %s', msg)

            echoStrat.snkPreUpdate(action=action, data=data)
            echoStrat.snkUpdate(action=action, data=data)
            echoStrat.snkPostUpdate(action=action, data=data)

        if agentOrderCon in socks:
            msg     = agentOrderCon.recv() # process order
            cmd     = json.loads(msg)
            logger.debug('AGENT: ORDER = %s', msg)

            cmds    = echoStrat.orderUpdate(cmd)
            echoStrat.addActionData( cmds )
            logger.debug('AGENT: COMMANDS = %s', cmds)

        if bbCon in socks:
            msg     = bbCon.recv() # process order
            cmd     = json.loads(msg)
            logger.debug('AGENT: BB = %s', cmd)

            signalName  = cmd['signalName']
            secName     = cmd['secName']
            symbol      = cmd['symbol']

            if secName == 'ECHO-PEND':
                cmd = dict( action=STRATSTATE.ORDERTYPE_SYMBOL_CANCEL, symbol=symbol, signalName=signalName)
            elif secName == 'ECHO-RLZD':
                cmd = dict( action=STRATSTATE.ORDERTYPE_SYMBOL_LIQUIDATE, symbol=symbol, signalName=signalName)
            else:
                errorMsg = 'Unknown secName=%s' % secName
                logger.error(errorMsg)
                raise ValueError(errorMsg)

            cmds    = echoStrat.bbOrderUpdate(cmds=[cmd])
            echoStrat.addActionData( cmds )
            logger.debug('AGENT: BB COMMANDS = %s', cmds)

        for cmd in echoStrat.getActionData():
            logger.debug('AGENT: SNKOUT = %s', cmd)
            msg = json.dumps(cmd)
            agentSinkOutCon.send(msg)

        if sigCon in socks:
            msg = sigCon.recv() # process signal
            logger.debug('AGENT: SIG = %s', msg)
            break

if __name__ == '__main__':
    '''
    -T turf
    -S strat
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-S", "--strat", help="strategy name", action="store")
    parser.add_argument("-T", "--turf",  help="turf name", action="store")
    args    = parser.parse_args()
    tweaks  = {
        'run_turf'  : args.turf,
        'agt_strat' : args.strat,
        'run_domain': 'echo_%s' % args.strat,
    }
    logger.debug( 'agent: turf=%s strat=%s', args.turf, args.strat)
    with twkcx.Tweaks( **tweaks ):
        run_agent()

'''
cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\agent.py --strat=ECHO1 --turf=ivp_redi_fix

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\agent.py --strat=ECHO2 --turf=ivp_redi_fix
'''
