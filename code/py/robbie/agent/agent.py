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
import robbie.echo.policy as stratpolicy
import robbie.echo.stratutil as stratutil
from   robbie.util.logging import logger

def register(context, regPort, agent, logName):
    regConn          = context.socket(zmq.REQ)
    regConn.connect("tcp://localhost:%s" % regPort)
    regConn.send('AGENT: %s: can i?' % agent)
    ok = regConn.recv()
    logger.debug('AGENT: REGISTER: %s, %s', logName, ok)

def run_agent():
    agent            = twkval.getenv('agt_strat')
    turf             = twkval.getenv('run_turf')

    policy           = stratpolicy.ScaleVenuePolicy( scale=.5, venue='GREY')

    signalMode       = turfutil.get(turf=turf, component='signal')
    agt_comm         = turfutil.get(turf=turf, component='communication', sub=agent)

    agent_execSrc    = agt_comm['agent_execSrc']
    port_sigCon      = agt_comm['agent_sigCon']
    agent_execSnkIn  = agt_comm['agent_execSnkIn']
    agent_execSnkOut = agt_comm['agent_execSnkOut']

    context          = zmq.Context()

    snkRegPort       = turfutil.get(turf=turf, component='communication', sub='SNK_REG')['port_reg']
    register(context, regPort=snkRegPort, agent=agent, logName='SNK')

    srcRegPort       = turfutil.get(turf=turf, component='communication', sub='SRC_REG')['port_reg']
    register(context, regPort=srcRegPort, agent=agent, logName='SRC')

    agentSrcInCon       = context.socket(zmq.SUB)
    agentSrcInCon.setsockopt(zmq.SUBSCRIBE, b'')
    agentSrcInCon.connect('tcp://localhost:%s' % agent_execSrc)

    sigCon = context.socket(zmq.SUB)
    sigCon.setsockopt(zmq.SUBSCRIBE, b'')
    sigCon.connect('tcp://localhost:%s' % port_sigCon)

    agentSinkOutCon      = context.socket(zmq.PAIR) # PUB
    agentSinkOutCon.bind('tcp://*:%s' % agent_execSnkOut)

    agentSinkInCon       = context.socket(zmq.PAIR) # SUB
    agentSinkInCon.connect('tcp://localhost:%s' % agent_execSnkIn)

    # Initialize poll set
    poller = zmq.Poller()
    poller.register(sigCon,         zmq.POLLIN)
    poller.register(agentSrcInCon,  zmq.POLLIN)
    poller.register(agentSinkInCon, zmq.POLLIN)

    if signalMode == stratutil.EXECUTION_MODE.NEW_FILL_CX:
        import robbie.echo.reflectstrat as reflectstrat
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
            action  = cmd[ 'action' ]
            data    = cmd[ 'data'   ]
            logger.debug('AGENT: SRCIN  = %s', msg)

            echoStrat.srcPreUpdate(action=action, data=data)
            echoStrat.srcUpdate(action=action, data=data)
            echoStrat.srcPostUpdate(action=action, data=data)

            for cmd in echoStrat.newMsg():
                logger.debug('AGENT: SNKOUT = %s', cmd)
                msg = json.dumps(cmd)
                agentSinkOutCon.send(msg)

        if agentSinkInCon in socks:
            msg     = agentSinkInCon.recv() # process task
            cmd     = json.loads(msg)
            action  = cmd['action']
            data    = cmd['data'  ]
            logger.debug('AGENT: SNKIN = %s', msg)

            echoStrat.snkPreUpdate(action=action, data=data)
            echoStrat.snkUpdate(action=action, data=data)
            echoStrat.snkPostUpdate(action=action, data=data)

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
c:\Python27\python2.7.exe robbie\agent\agent.py --strat=ECHO1 --turf=dev

cd C:\Users\ilya\GenericDocs\dev\quad\code\py
c:\Python27\python2.7.exe robbie\agent\agent.py --strat=ECHO2 --turf=dev
'''

'''
form sink =  {
    "orderId"    : "20160621_182343",
    "action"     : "new",
    "execTime"   : "20160621-22:23:43.556",
    "price"      : 0,
    "signalName" : "ECHO1",
    "symbol"     : "IBM",
    "qty"        : 1000}

from src  =  {
    "orderId"    : "20160621_182343",
    "action"     : "fill",
    "execTime"   : "TIME",
    "price"      : 200.0,
    "signalName" : "ECHO1",
    "symbol"     : "IBM",
    "qty"        : 200}

'''
