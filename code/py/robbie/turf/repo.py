'''
TYPE:       : lib
DESCRIPTION : turf.repo module
AUTHOR      : ilya presman, 2016
'''

from   robbie.echo.stratutil import EXECUTION_MODE

_p = 5000
def nextport():
    ''' nextport '''
    global _p
    _p += 1
    return _p

def newAgent():
    '''  newAgent '''
    return {
        'agent_execSrc'      : nextport(),
        'agent_sigCon'       : nextport(),
        'agent_execSnkIn'    : nextport(),
        'agent_execSnkOut'   : nextport(),
    }

def newSrcCmd():
    return {
        'port_cmd' : nextport(),
    }

def newSinkReg():
    return {
        'port_reg' : nextport(),
    }

_conf = {
    'dev': {
        'signal': EXECUTION_MODE.FILL_ONLY,
        'cmd': [
            'CMD'
        ],
        'agents': [
            'ECHO1',
            'ECHO2'
        ],
        'communication' : {
            'SNK_REG'      : newSinkReg(),
            'SRC_REG'       : newSinkReg(),
            'SNK_CMD'       : newSrcCmd(),
            'SRC_CMD'       : newSrcCmd(),
            'ECHO1'         : newAgent(),
            'ECHO2'         : newAgent(),
        },
        'shared_location': {
            'domain'     : 'echo',
        }
    },
    'example_turf': {
        'shared_location': {
            'domain'     : 'example',
        }
    }
}

