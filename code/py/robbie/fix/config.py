'''
TYPE         : lib
OWNER        : ilya
DESCCRIPTION : [quick]FIX related configuration
'''

import os

import robbie.util.misc as libmisc
import robbie.tweak.value as twkval
from   robbie.util.logging import logger

fixVersion_4_2='FIX.4.2'

def getFIXConfig( tag ):
    global fixVersion_4_2
    
    dn = twkval.getenv( 'fix_root' )
    
    if tag in [ 'store', 'log', 'config' ]:        
        path = os.path.join( dn, tag )
        
        if not os.path.exists( path ):
            logger.debug( 'getFIXConfig: creating: %s' % path )
            libmisc.makeMissingDirs( dirName=path )
        
        if tag  == 'config':
            return os.path.join( path, 'fixconnect.cfg')
        else:
            return path

    raise ValueError( 'Unknown env=%s tag=%s' % ( str(tag) ) )

def configContent( fixDictPath, logPath, storePath, host, port, sender, target, fixVersion=fixVersion_4_2 ):
    '''supply content for the FIX config'''

    content = '''[DEFAULT]
BeginString=%s
FileLogPath=%s
FileStorePath=%s
FileLogHeartbeats=Y
HeartBtInt=60
UseLocalTime=Y
DataDictionary=%s
MillisecondsInTimeStamp=N

[SESSION]
ConnectionType=initiator
ReconnectInterval=60
SocketConnectPort=%s
SocketConnectHost=%s
SenderCompID=%s
TargetCompID=%s
StartTime=08:35:00
EndTime=08:30:00
RefreshOnLogon=Y
'''
    return content % ( fixVersion, logPath, storePath, fixDictPath, port, host, sender, target )

def createConfigFile( content, override=False ):
    fnfixconfig = getFIXConfig( tag='config'  )

    with open( fnfixconfig, 'w' ) as fd:
        fd.write( content )
        
    return fnfixconfig

