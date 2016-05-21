'''
TYPE:       : lib
DESCRIPTION : turf.repo module
AUTHOR      : ilya presman, 2016
'''
_p = 5000
def nextport():
    global _p
    _p += 1
    return _p

_conf = {
    'dev': {
        'agents': [ 'ECHO1'],
        'communication': {
            'ECHO1' : {
                'port_execSrc'      : nextport(),
                'port_sigCon'       : nextport(),
                'port_execSnkIn'    : nextport(),
                'port_execSnkOut'   : nextport(),
            },
            'ECHO2' : {
                'port_execSrc'      : nextport(),
                'port_sigCon'       : nextport(),
                'port_execSnkIn'    : nextport(),
                'port_execSnkOut'   : nextport(),
            }

        }
    }
}

