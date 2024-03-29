'''
TYPE         : lib
OWNER        : ilya
DESCCRIPTION : [quick]FIX related configuration
'''

import os
import shutil

import robbie.util.misc as libmisc
from   robbie.util.logging import logger

fixVersion_4_2='FIX.4.2'

def getFIXConfig( root, name, cleanSlate=False ):

    if name in [ 'store', 'log', 'config' ]:
        path = os.path.join( root, name )
        if not os.path.exists( path ):
            logger.debug( 'getFIXConfig: making: %s' % path )
            libmisc.makeMissingDirs( dirName=path )

        if name  == 'config':
            fullPath = os.path.join( path, 'fixconnect.cfg')
        else:
            fullPath = path

        if os.path.exists( fullPath ):
            if cleanSlate:
                logger.debug( 'getFIXConfig: removing: %s' % path )
                shutil.rmtree( fullPath )

        return fullPath
    else:
        raise ValueError( 'Unknown env=%s tag=%s' % ( str(name) ) )

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
StartTime=00:00:00
EndTime=00:00:00
RefreshOnLogon=Y
'''
    return content % ( fixVersion, logPath, storePath, fixDictPath, port, host, sender, target )

def createConfigFile( root, content, override=False ):
    fnfixconfig = getFIXConfig( root=root, name='config'  )

    with open( fnfixconfig, 'w' ) as fd:
        fd.write( content )
        
    return fnfixconfig