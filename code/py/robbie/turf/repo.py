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
        'port_execSrc'      : nextport(),
        'port_sigCon'       : nextport(),
        'port_execSnkIn'    : nextport(),
        'port_execSnkOut'   : nextport(),
    }

def newSrcCmd():
    return {
        'port_cmd' : nextport(),
    }

_conf = {
    'dev': {
        'execsrccmd': [ 'SRCCMD' ],
        'agents'    : [ 'ECHO1', 'ECHO2'  ],
        'communication': {
            'SRCCMD'    : newSrcCmd(),
            'ECHO1'     : newAgent(),
            'ECHO2'     : newAgent(),
        }
    },
    'example_turf': {
        'shared_location': {
            'domain'     : 'example',
        }
    }
}

