'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.compat module
'''

'''
various compatibility flags
'''

import os
import sys
import platform
import traceback
import functools
from robbie.util.logging import logger

_checks = {}

def isGenWrapper( name, func, *args ):
    def isNameWrapped():
        global _checks
        if name in _checks:
            return _checks[ name ]
        try:
            _checks[ name ] = func( *args )
        except:
            _checks[ name ] = False
            logger.error( 'COMPAT BEGIN --------------------------------------------' )
            logger.error( traceback.format_exc() )
            logger.error( 'COMPAT END   --------------------------------------------' )
            return False
        return _checks[ name ]
    return isNameWrapped

def _isweavable():
    from scipy import weave
    a = 1
    weave.inline('printf("%d\\n",a);',['a'])
    return True

isweavable = isGenWrapper( 'isweavable', _isweavable )

def needsLocalData():
    '''indicate that we are working from a win32'''
    platform = sys.platform
    return ( platform == 'win32' )

def hasModule( moduleName ):
    '''indicate that we are working from a win32'''
    if moduleName == 'fcntl':
        platform = sys.platform
        return (  'linux' in platform )

    raise ValueError( 'Unknown module = %s' % str( moduleName ) )

def isWin32():
    '''is this a windows platform'''
    platform = sys.platform
    return ( 'win' in platform )

def isLinux():
    '''is this a linux platform'''
    platform = sys.platform
    return ( 'linux' in platform )

def mustHaveEnv( twkName, envName ):
    v = os.getenv(envName)
    if v:
        return v
    else:
        raise ValueError('Must have env=%s for tweak=%s' % ( envName, twkName ) )

def twkgetenv(name):
    return functools.partial(getenv, name)

def getenv( name ):
    ''' link from tweak to the os '''
    name = name.lower()
    if name in ( 'env_origusername', 'env_username' ):
        if isWin32():
            return os.getenv('UserName')
        else:
            return os.getenv('USER')
    elif name == 'run_margotroot':
        return mustHaveEnv( name, 'QUAD_MARGOT_ROOT' )
    elif name == 'run_configroot':
        return mustHaveEnv( name, 'QUAD_CONFIG_ROOT' )
    raise ValueError( 'Unknown name = %s' % name )

def ping(hostName, count):
    '''windows and linux have different ping arguments/default behavior!'''
    if isWin32():
        return 'ping',  ( '-n %d' % count, hostName )
    else:
        return 'ping', ( '-c %d' % count, hostName )

def node():
    return platform.node().split('.')[0]

