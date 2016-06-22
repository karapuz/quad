'''
TYPE:       : lib
DESCRIPTION : turf.repo module
AUTHOR      : ilya presman, 2016
'''

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
        'execsrccmd': [ 'SRCCMD' ],
        'agents'    : [ 'ECHO1', 'ECHO2'  ],
        'communication': {
            'SINK_REGISTER'  : newSinkReg(),
            'SRCCMD'    : newSrcCmd(),
            'SINKCMD'   : newSrcCmd(),
            'ECHO1'     : newAgent(),
            'ECHO2'     : newAgent(),
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

