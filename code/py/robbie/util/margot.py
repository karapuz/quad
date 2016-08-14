'''
AUTHOR      : ilya presman, 2016
TYPE:       : lib
DESCRIPTION : util.margot module
'''

import os
import threading
import robbie.util.misc as libmisc
import robbie.tweak.value as twkval
from   robbie.util.logging import logger

_getMargotRootLock = threading.Lock()
def getMargotRoot( create=True):
    with _getMargotRootLock:
        return _getMargotRoot( create=create)

def getConfigRoot(name, debug=True):
    '''
    provide space for config data
    QUAD_CONFIG_ROOT: c:\users\ilya\GenericDocs\dev\quad\data\config
    '''
    return os.path.join( twkval.getenv( 'run_configRoot' ), name )

def _getMargotRoot( create=True):
    '''
    provide space for margot data
    QUAD_MARGOT_ROOT: c:\users\ilya\GenericDocs\dev\data\margot
    QUAD_CONFIG_ROOT: c:\users\ilya\GenericDocs\dev\quad\data\config
    '''
    root = twkval.getenv( 'run_margotRoot' ) or os.getenv( 'QUAD_MARGOT_ROOT' )
    try:
        if create and not os.path.exists( root ):
            libmisc.makeMissingDirs( dirName=root )
    except OSError:
        if not os.path.exists( root ):
            logger.error( 'margot: root does not exist, but get OSError')
            raise
    return root

def getSessionSlice( domain, user, session, activity, create=True, debug=True ):
    ''' '''

    root  = _getSharedRoot( domain=domain, user=user, session=session, create=create )
    path = os.path.join( root, '%s.mmap' % activity )
    if debug:
        logger.debug('session_slice: path=%s', path)
    return path

def _getSharedRoot( domain, user, session, create=True ):
    ''' '''
    varDir = os.path.join( getMargotRoot(), 'shared', domain, user, session )

    if create:
        libmisc.makeMissingDirs( dirName=varDir )
    return varDir

def _getLogRoot( domain, user, session, create=True ):
    ''' '''
    varDir = os.path.join( getMargotRoot(), 'log', domain, user, session )

    if create:
        libmisc.makeMissingDirs( dirName=varDir )
    return varDir

def _getRoot( compName, debug=False ):
    ''' find margot path '''    
    dn      = getMargotRoot()
    today   = str( twkval.getenv( 'today' ) )
    source  = twkval.getenv( 'fix_source' )
    comps   = set( [  'fix', 'run', 'command', 'bloomberg'  ] )
    
    if compName in comps:
        path    = os.path.join( dn, today, compName )
    else:
        raise ValueError( 'Unknown compName=%s' % compName )
    
    if debug:
        logger.debug( '_getRoot: compName=%s path=%s' % ( compName, path ) )
    return path

def getRoot( compName, create=True, debug=True ):
    ''' create directory structure
        compName = [ bob | cached-calibs ]
        margot/bob/init
    '''
    path    = _getRoot( compName=compName, debug=debug )
    if create:
        libmisc.makeMissingDirs( dirName=path )
    return path

