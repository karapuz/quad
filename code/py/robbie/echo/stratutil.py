'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : echo.stratutil module
DESCRIPTION : this module contains utilities for strategies
'''

from   robbie.util.logging import logger

class STRATSTATE(object):

    ''' state '''
    CLOSING = 'CLOSING STATE'
    OPENING = 'OPENING STATE'
    EMPTY   = 'EMPTY STATE'

    ''' action '''
    ISSUEOPENORDER  = 'ISSUE OPEN ORDER'
    ISSUECLOSEORDER = 'ISSUE CLOSE ORDER'

def _sign(x):
    if x == 0:
        return None
    if x > 0:
        return 1
    else:
        return -1

def getAction(state, sign, qty):
    ''' getAction '''

    if state == STRATSTATE.EMPTY:
        nextAction  = STRATSTATE.ISSUEOPENORDER
        nextState   = STRATSTATE.OPENING
    elif state == STRATSTATE.OPENING:
        if qty * sign > 0:
            nextAction  = STRATSTATE.ISSUEOPENORDER
            nextState   = STRATSTATE.OPENING
        else:
            nextAction  = STRATSTATE.ISSUECLOSEORDER
            nextState   = STRATSTATE.CLOSING
    elif state == STRATSTATE.CLOSING:
            nextAction  = None
            nextState   = STRATSTATE.CLOSING
    else:
        logger.error('_getAction: Unknown state=%s', state)
        nextAction  = None
        nextState   = None
    return nextState, nextAction

def getCurrentState(pendingPos, realizedPos):
    ''' getCurrentState '''
    if pendingPos:
        if realizedPos:
            if pendingPos * realizedPos < 0:
                state =  STRATSTATE.CLOSING
                sign  = _sign(0)
            else:
                state =  STRATSTATE.OPENING
                sign  = _sign(pendingPos)
        else:
            state =  STRATSTATE.OPENING
            sign  = _sign(pendingPos)
    else:
        if realizedPos:
            state =  STRATSTATE.OPENING
            sign  = _sign(realizedPos)
        else:
            state =  STRATSTATE.EMPTY
            sign  = _sign(0)

    return state, sign
