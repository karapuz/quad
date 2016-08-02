'''
TYPE:       : lib
DESCRIPTION : turf.repo module
AUTHOR      : ilya presman, 2016
'''
import copy
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
        #'agent_orderCmd'     : nextport(),
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
            'REDI'          : newSrcCmd(),
            'SNK_REG'       : newSinkReg(),
            'SRC_REG'       : newSinkReg(),
            'SNK_CMD'       : newSrcCmd(),
            'SRC_CMD'       : newSrcCmd(),
            'ECHO1'         : newAgent(),
            'ECHO2'         : newAgent(),
        },
        'shared_location': {
            'domain'     : 'echo',
        },
        'pricestrip':{
            'domain' : 'echo',
            'user'   : 'bbg',
        },
        'fix_SrcConnConfig' : {
            'host'  : 'localhost',
            'port'  : 9878,
            'sender': 'BANZAI',
            'target': 'FIXIMULATOR',
        },
        'fix_SinkConnConfig' : {
            'host'  : 'localhost',
            'port'  : 9888,
            'sender': 'BANZAISINK',
            'target': 'FIXIMULATORSINK',
        },
    },
    'example_turf': {
        'shared_location': {
            'domain'     : 'example',
        }
    }
}

_conf[ 'dev_full' ] = copy.deepcopy(_conf[ 'dev' ])
_conf[ 'dev_full' ]['signal'] = EXECUTION_MODE.NEW_FILL_CX

###
# QUAD drop copy
#
_conf[ 'dev_quad' ] = copy.deepcopy(_conf[ 'dev_full' ])
_conf[ 'dev_quad' ][ 'fix_SrcConnConfig' ] = {
            'host'  : '207.17.44.100',
            'port'  : 40000,
            'sender': 'QUADEQTRPTS',
            'target': 'REDIRPT',
        }
