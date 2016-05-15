'''
lib.tmp module
'''

import os
import sys
import tempfile
import datetime
import robbie.util.misc as libmisc
import robbie.util.calendar as calendar

def getTempFile( app, suffix, dn = None ):
    '''provide temp file space for chloe applications'''
    dn  = dn or getUserTempRoot()
    now = str( calendar.today() )
    return tempfile.mkstemp(prefix='%s_%s_' % ( now, app ), dir=dn, suffix=suffix )[ 1 ]

def getTempTimeFile( app, suffix, dn = None ):
    '''provide temp file space for chloe applications'''
    dn  = dn or getUserTempRoot()
    now = datetime.datetime.now().strftime( '%Y%d%m%H%M%S%f' )
    return os.path.join( dn, '%s_%s.%s' % ( app, now, suffix  ) )

def _getTempDir( app, suffix, style ):
    '''provide temp dir space for chloe applications'''
    dn      = getUserTempRoot()
    now     = str( calendar.today() )
    if style == 'long':
        return tempfile.mkdtemp(prefix = '%s_%s_' % ( now, app ), dir=dn, suffix=suffix )
    elif style == 'mid':
        dn = os.path.join( dn, now )
        libmisc.makeMissingDirs( dirName=dn )
        return tempfile.mkdtemp( prefix=app, dir=dn, suffix=suffix )
    elif style == 'short':
        dn = os.path.join( dn, now, app )
        libmisc.makeMissingDirs( dirName=dn )
        return tempfile.mkdtemp( dir=dn, suffix=suffix )

def getTempDir( app, suffix='' ):
    '''provide temp dir space for chloe applications'''
    return _getTempDir( app, suffix, style='long' )

def getTempLongDir( app, suffix='' ):
    '''provide temp dir space for chloe applications'''
    return _getTempDir( app, suffix, style='short' )

def getTempMidDir( app, suffix='' ):
    '''provide temp dir space for chloe applications'''
    return _getTempDir( app, suffix, style='mid' )

def getUserTempRoot( userName=None, create=True, tail=None ):
    '''provide temp space for chloe applications'''

    if userName == None:
        import robbie.tweak.value as twval
        userName = twval.getenv( 'env_userName' )
        
    platform = sys.platform
    if platform == 'win32':
        dn = 'c:\\temp\\robbie\\%s' % userName
    elif platform == 'linux2':
        dn = '/tmp/robbie/%s' % userName
    else:
        raise ValueError( 'Unimplemented platform')

    if tail:
        dn = os.path.join( dn, tail )
            
    if create:
        libmisc.makeMissingDirs( dirName=dn )

    return dn

def getTempRoot( sub=None ):
    '''provide temp space root '''
    platform = sys.platform
    if platform == 'win32':
        dn          = 'c:\\temp' 
    elif platform == 'linux2':
        dn = '/tmp'
    else:
        raise ValueError( 'Unimplemented platform')
    libmisc.makeMissingDirs( dirName=dn )
    if sub:
        dn = os.path.join( dn, sub )
        libmisc.makeDirsIfNotExists( dn )
    return dn

def getTrueTempFile( app, suffix ):
    '''provide temp file space for chloe applications'''
    dn  = getTempRoot()
    now = str( calendar.today() )
    return tempfile.mkstemp(prefix='%s_%s_' % ( now, app ), dir=dn, suffix=suffix )[ 1 ]
