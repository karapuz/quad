'''
util.compat module
'''

'''
various compatibility flags
'''

import sys
import os
import platform
import traceback
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

def getenv( name ):
    name = name.lower()
    if name in ( 'env_origusername', 'env_username' ):
        if isWin32():
            return os.getenv('UserName')
        else:
            return os.getenv('USER')
    raise ValueError( 'Unknown name = %s' % name )

def ping(hostName, count):
    '''windows and linux have different ping arguments/default behavior!'''
    if isWin32():
        return 'ping',  ( '-n %d' % count, hostName )
    else:
        return 'ping', ( '-c %d' % count, hostName )

def node():
    return platform.node().split('.')[0]

